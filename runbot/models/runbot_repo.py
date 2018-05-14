import os
import re
import logging
import subprocess
import time
import datetime
import dateutil.parser
import signal

import requests
import json

from odoo import models, fields, api
from odoo.tools import config

from .tools import fqdn, run, dt2time, mkdirs

_logger = logging.getLogger(__name__)


class RunbotRepo(models.Model):
    _name = "runbot.repo"
    _order = 'id'
    
    name = fields.Char('Repository', required=True)
    path = fields.Char(string='Directory', readonly=1, compute='_compute_path_base')
    base = fields.Char(string='Base URL', readonly=1, compute='_compute_path_base')
    nginx = fields.Boolean('Nginx')
    mode = fields.Selection([('disabled', 'Disabled'),
                             ('poll', 'Poll'),
                             ('hook', 'Hook')],
                            string="Mode", required=True, default='poll',
                            help="hook: Wait for webhook on /runbot/hook/<id> i.e. github push event")
    hook_time = fields.Datetime('Last hook time')
    duplicate_id = fields.Many2one('runbot.repo', 'Duplicate repo', help='Repository for finding duplicate builds')
    modules = fields.Char("Modules to install", help="Comma-separated list of modules to install and test.")
    modules_auto = fields.Selection([('none', 'None (only explicit modules list)'),
                                     ('repo', 'Repository modules (excluding dependencies)'),
                                     ('all', 'All modules (including dependencies)')],
                                    string="Other modules to install automatically", default='repo')
    dependency_ids = fields.Many2many(
        'runbot.repo', 'runbot_repo_dep_rel',
        column1='dependant_id', column2='dependency_id',
        string='Extra dependencies',
        help="Community addon repos which need to be present to run tests.")
    token = fields.Char("Github token")
    group_ids = fields.Many2many('res.groups', string='Limited to groups')

    @api.depends('name')
    def _compute_path_base(self):
        root = self.root()
        for r in self:
            name = r.name
            for i in '@:/':
                name = name.replace(i, '_')
            r.path = os.path.join(root, 'repo', name)

            name = re.sub('.+@', '', r.name)
            r.base = re.sub('.git$', '', name).replace(':', '/')

    @api.model
    def root(self):
        """Return root directory of repository"""
        default = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        return self.env['ir.config_parameter'].get_param('runbot.root', default)

    @api.model
    def domain(self):
        domain = self.env['ir.config_parameter'].get_param('runbot.domain', fqdn())
        return domain

    @api.multi
    def git(self, cmd):
        """Execute git command cmd"""
        self.ensure_one()
        cmd = ['git', '--git-dir=%s' % self.path] + cmd
        _logger.info("git: %s", ' '.join(cmd))
        return subprocess.check_output(cmd)

    @api.multi
    def git_export(self, treeish, dest):
        for repo in self:
            _logger.debug('checkout %s %s %s', repo.name, treeish, dest)
            p1 = subprocess.Popen(['git', '--git-dir=%s' % repo.path, 'archive', treeish], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(['tar', '-xC', dest], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
            p2.communicate()[0]

    def github(self, url, payload=None, ignore_errors=False):
        """Return a http request to be sent to github"""
        for repo in self:
            if not repo.token:
                return
            try:
                match_object = re.search('([^/]+)/([^/]+)/([^/.]+(.git)?)', repo.base)
                if match_object:
                    url = url.replace(':owner', match_object.group(2))
                    url = url.replace(':repo', match_object.group(3))
                    url = 'https://api.%s%s' % (match_object.group(1), url)
                    session = requests.Session()
                    session.auth = (repo.token, 'x-oauth-basic')
                    session.headers.update({'Accept': 'application/vnd.github.she-hulk-preview+json'})
                    if payload:
                        response = session.post(url, data=json.dumps(payload))
                    else:
                        response = session.get(url)
                    response.raise_for_status()
                    return response.json()
            except Exception:
                if ignore_errors:
                    _logger.exception('Ignored github error %s %r', url, payload)
                else:
                    raise

    @api.multi
    def update(self, values):
        super().update(values)
        for repo in self:
            self.update_git(repo)

    @api.model
    def update_git(self, repo):
        _logger.debug('repo %s updating branches', repo.name)

        Build = self.env['runbot.build']
        Branch = self.env['runbot.branch']

        if not os.path.isdir(os.path.join(repo.path)):
            os.makedirs(repo.path)
        if not os.path.isdir(os.path.join(repo.path, 'refs')):
            run(['git', 'clone', '--bare', repo.name, repo.path])

        # check for mode == hook
        fname_fetch_head = os.path.join(repo.path, 'FETCH_HEAD')
        if os.path.isfile(fname_fetch_head):
            fetch_time = os.path.getmtime(fname_fetch_head)
            if repo.mode == 'hook' and repo.hook_time and dt2time(repo.hook_time) < fetch_time:
                t0 = time.time()
                _logger.debug('repo %s skip hook fetch fetch_time: %ss ago hook_time: %ss ago',
                              repo.name, int(t0 - fetch_time), int(t0 - dt2time(repo.hook_time)))
                return

        repo.git(['gc', '--auto', '--prune=all'])
        repo.git(['fetch', '-p', 'origin', '+refs/heads/*:refs/heads/*'])
        repo.git(['fetch', '-p', 'origin', '+refs/pull/*/head:refs/pull/*'])

        fields = ['refname', 'objectname', 'committerdate:iso8601', 'authorname', 'authoremail', 'subject',
                  'committername', 'committeremail']
        fmt = "%00".join(["%(" + field + ")" for field in fields])
        git_refs = repo.git(['for-each-ref', '--format', fmt, '--sort=-committerdate', 'refs/heads', 'refs/pull'])
        git_refs = git_refs.strip()

        refs = [[field for field in line.split('\x00')] for line in git_refs.split('\n')]

        for name, sha, date, author, author_email, subject, committer, committer_email in refs:
            # create or get branch
            branch_ids = Branch.search([('repo_id', '=', repo.id), ('name', '=', name)])
            if branch_ids:
                branch = branch_ids[0]
            else:
                _logger.debug('repo %s found new branch %s', repo.name, name)
                branch = Branch.create({'repo_id': repo.id, 'name': name})
            # skip build for old branches
            if dateutil.parser.parse(date[:19]) + datetime.timedelta(30) < datetime.datetime.now():
                continue
            # create build (and mark previous builds as skipped) if not found
            build_ids = Build.search([('branch_id', '=', branch.id), ('name', '=', sha)])
            if not build_ids:
                _logger.debug('repo %s branch %s new build found revno %s', branch.repo_id.name, branch.name, sha)
                build_info = {
                    'branch_id': branch.id,
                    'name': sha,
                    'author': author,
                    'author_email': author_email,
                    'committer': committer,
                    'committer_email': committer_email,
                    'subject': subject,
                    'date': dateutil.parser.parse(date[:19]),
                }

                if not branch.sticky:
                    skipped_build_sequences = Build.search_read(
                        [('branch_id', '=', branch.id), ('state', '=', 'pending')],
                        fields=['sequence'], order='sequence asc')
                    if skipped_build_sequences:
                        to_be_skipped_ids = [build['id'] for build in skipped_build_sequences]
                        Build.browse(to_be_skipped_ids).skip()
                        # new order keeps lowest skipped sequence
                        build_info['sequence'] = skipped_build_sequences[0]['sequence']
                Build.create(build_info)

        # skip old builds (if their sequence number is too low, they will not ever be built)
        skippable_domain = [('repo_id', '=', repo.id), ('state', '=', 'pending')]
        icp = self.pool['ir.config_parameter']
        running_max = int(icp.get_param('runbot.running_max', default=75))
        to_be_skipped_ids = Build.search(skippable_domain, order='sequence desc', offset=running_max)
        Build.browse(to_be_skipped_ids).skip()

    def scheduler(self):
        icp = self.env['ir.config_parameter']
        workers = int(icp.get_param('runbot.workers', default=6))
        running_max = int(icp.get_param('runbot.running_max', default=75))
        host = fqdn()

        Build = self.env['runbot.build']
        domain = [('repo_id', 'in', self.ids)]
        domain_host = domain + [('host', '=', host)]

        # schedule jobs (transitions testing -> running, kill jobs, ...)
        build_ids = Build.search(domain_host + [('state', 'in', ['testing', 'running'])])
        build_ids.schedule()

        # launch new tests
        testing = Build.search_count(domain_host + [('state', '=', 'testing')])
        pending = Build.search_count(domain + [('state', '=', 'pending')])

        while testing < workers and pending > 0:

            # find sticky pending build if any, otherwise, last pending (by id, not by sequence) will do the job
            pending_ids = Build.search(domain + [('state', '=', 'pending'), ('branch_id.sticky', '=', True)], limit=1)
            if not pending_ids:
                pending_ids = Build.search(domain + [('state', '=', 'pending')], order="sequence", limit=1)
            pending_ids.schedule()

            # compute the number of testing and pending jobs again
            testing = Build.search_count(domain_host + [('state', '=', 'testing')])
            pending = Build.search_count(domain + [('state', '=', 'pending')])

        # terminate and reap doomed build
        build_ids = Build.search(domain_host + [('state', '=', 'running')])
        # sort builds: the last build of each sticky branch then the rest
        sticky = {}
        non_sticky = []
        for build in build_ids:
            if build.branch_id.sticky and build.branch_id.id not in sticky:
                sticky[build.branch_id.id] = build.id
            else:
                non_sticky.append(build.id)
        build_ids = sticky.values()
        build_ids += non_sticky
        # terminate extra running builds
        build_ids[running_max:].kill()
        build_ids.reap()

    @api.model
    def reload_nginx(self):
        settings = {}
        settings['port'] = config['xmlrpc_port']
        nginx_dir = os.path.join(self.root(), 'nginx')
        settings['nginx_dir'] = nginx_dir
        ids = self.search([('nginx', '=', True)], order='id')
        if ids:
            settings['builds'] = self.env['runbot.build'].search([('repo_id', 'in', ids), ('state', '=', 'running')])

            nginx_config = self.env['ir.ui.view'].render("runbot.nginx_config", settings)
            mkdirs([nginx_dir])
            open(os.path.join(nginx_dir, 'nginx.conf'), 'w').write(nginx_config)
            try:
                _logger.debug('reload nginx')
                pid = int(open(os.path.join(nginx_dir, 'nginx.pid')).read().strip(' \n'))
                os.kill(pid, signal.SIGHUP)
            except Exception:
                _logger.debug('start nginx')
                if run(['/usr/sbin/nginx', '-p', nginx_dir, '-c', 'nginx.conf']):
                    # obscure nginx bug leaving orphan worker listening on nginx port
                    if not run(['pkill', '-f', '-P1', 'nginx: worker']):
                        _logger.debug('failed to start nginx - orphan worker killed, retrying')
                        run(['/usr/sbin/nginx', '-p', nginx_dir, '-c', 'nginx.conf'])
                    else:
                        _logger.debug('failed to start nginx - failed to kill orphan worker - oh well')

    @api.model
    def killall(self):
        # kill switch
        Build = self.env['runbot.build']
        build_ids = Build.search([('state', 'not in', ['done', 'pending'])])
        build_ids.kill()

    @api.model
    def cron(self):
        all_repo = self.search([('mode', '!=', 'disabled')])
        all_repo.update()
        all_repo.scheduler()
        self.reload_nginx()
