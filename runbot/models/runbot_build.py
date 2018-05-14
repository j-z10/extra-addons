import logging
import re
import subprocess
import operator
import time
import os
import shutil
import glob
import sys
import resource
import signal

from odoo import models, fields, api
from odoo.tools import config, appdirs, DEFAULT_SERVER_DATETIME_FORMAT

from .tools import dashes, dt2time, uniq_list, mkdirs, local_pgadmin_cursor, run, grep, lock, locked, rfind, fqdn

_logger = logging.getLogger(__name__)
_re_error = r'^(?:\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3} \d+ (?:ERROR|CRITICAL) )|(?:Traceback \(most recent call last\):)$'
_re_warning = r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3} \d+ WARNING '
_re_job = re.compile('job_\d')


class RunbotBuild(models.Model):
    _name = "runbot.build"
    _order = 'id desc'

    branch_id = fields.Many2one('runbot.branch', 'Branch', required=True, ondelete='cascade')
    repo_id = fields.Many2one('runbot.repo', string='Repository', related='branch_id.repo_id')
    name = fields.Char('Revno', required=True)
    host = fields.Char('Host')
    port = fields.Integer('Port')
    dest = fields.Char(compute='_compute_dest_domain', string='Dest', readonly=1, store=True)
    domain = fields.Char(compute='_compute_dest_domain', string='URL')
    date = fields.Datetime('Commit date')
    author = fields.Char('Author')
    author_email = fields.Char('Author Email')
    committer = fields.Char('Committer')
    committer_email = fields.Char('Committer Email')
    subject = fields.Text('Subject')
    sequence = fields.Integer('Sequence')
    modules = fields.Char("Modules to Install")
    result = fields.Char('Result')  # ok, ko, warn, skipped, killed
    pid = fields.Integer('Pid')
    state = fields.Char('Status', default='pending')  # pending, testing, running, done, duplicate
    job = fields.Char('Job')  # job_*
    job_start = fields.Datetime('Job start')
    job_end = fields.Datetime('Job end')
    job_time = fields.Integer(compute='_compute_time_age', string='Job time')
    job_age = fields.Integer(compute='_compute_time_age', string='Job age')
    duplicate_id = fields.Many2one('runbot.build', 'Corresponding Build')
    server_match = fields.Selection([('builtin', 'This branch includes Odoo server'),
                                     ('exact', 'branch/PR exact name'),
                                     ('prefix', 'branch whose name is a prefix of current one'),
                                     ('fuzzy', 'Fuzzy - common ancestor found'),
                                     ('default', 'No match found - defaults to master')],
                                    string='Server branch matching')

    @api.depends('branch_id')
    def _compute_dest_domain(self):
        domain = self.env['runbot.repo'].domain()
        for build in self:
            nickname = dashes(build.branch_id.name.split('/')[2])[:32]
            build.dest = "%05d-%s-%s" % (build.id, nickname, build.name[:6])
            if build.repo_id.nginx:
                build.domain = "%s.%s" % (build.dest, build.host)
            else:
                build.domain = "%s:%s" % (domain, build.port)

    @api.depends('job_end', 'job_start')
    def _compute_time_age(self):
        for r in self:
            if r.job_end:
                r.job_time = int(dt2time(r.job_end) - dt2time(r.job_start))
            elif r.job_start:
                r.job_time = int(time.time() - dt2time(r.job_start))

            if r.job_start:
                r.job_age = int(time.time() - dt2time(r.job_start))

    def create(self, value):
        build = super().create(value)
        extra_info = {'sequence': build.id}

        # detect duplicate
        domain = [
            ('repo_id', '=', build.repo_id.duplicate_id.id),
            ('name', '=', build.name),
            ('duplicate_id', '=', False),
            '|', ('result', '=', False), ('result', '!=', 'skipped')
        ]
        duplicate_build = self.search(domain)

        if duplicate_build:
            extra_info.update({'state': 'duplicate', 'duplicate_id': duplicate_build.ids[0]})
            duplicate_build.write({'duplicate_id': build.id})
        build.write(extra_info)

    def reset(self):
        self.write({'state': 'pending'})

    def logger(self, *l):
        l = list(l)
        for build in self:
            l[0] = "%s %s" % (build.dest, l[0])
            _logger.debug(*l)

    def list_jobs(self):
        return sorted(job for job in dir(self) if _re_job.match(job))

    @api.model
    def find_port(self):
        # currently used port
        ports = set(i['port'] for i in self.search_read([('state', 'not in', ['pending', 'done'])], ['port']))

        # starting port
        icp = self.env['ir.config_parameter']
        port = int(icp.get_param('runbot.starting_port', default=2000))

        # find next free port
        while port in ports:
            port += 2

        return port

    def _get_closest_branch_name(self, target_repo_id):
        """Return (repo, branch name) of the closest common branch between build's branch and
           any branch of target_repo or its duplicated repos.

        Rules priority for choosing the branch from the other repo is:
        1. Same branch name
        2. A PR whose head name match
        3. Match a branch which is the dashed-prefix of current branch name
        4. Common ancestors (git merge-base)
        Note that PR numbers are replaced by the branch name of the PR target
        to prevent the above rules to mistakenly link PR of different repos together.
        """
        self.ensure_one()
        branch_model = self.env['runbot.branch']

        branch, repo = self.branch_id, self.repo_id
        pi = branch._get_pull_info()
        name = pi['base']['ref'] if pi else branch.branch_name

        target_repo = self.env['runbot.repo'].browse(target_repo_id)

        target_repo_ids = [target_repo.id]
        r = target_repo.duplicate_id
        while r:
            if r.id in target_repo_ids:
                break
            target_repo_ids.append(r.id)
            r = r.duplicate_id

        _logger.debug('Search closest of %s (%s) in repos %r', name, repo.name, target_repo_ids)

        sort_by_repo = lambda d: (not d['sticky'],      # sticky first
                                  target_repo_ids.index(d['repo_id'][0]),
                                  -1 * len(d.get('branch_name', '')),
                                  -1 * d['id'])
        result_for = lambda d, match='exact': (d['repo_id'][0], d['name'], match)
        branch_exists = lambda d: branch_model.browse(d['id'])._is_on_remote()
        fields = ['name', 'repo_id', 'sticky']

        # 1. same name, not a PR
        domain = [
            ('repo_id', 'in', target_repo_ids),
            ('branch_name', '=', name),
            ('name', '=like', 'refs/heads/%'),
        ]
        targets = branch_model.search_read(domain, fields, order='id DESC')
        targets = sorted(targets, key=sort_by_repo)
        if targets and branch_exists(targets[0]):
            return result_for(targets[0])

        # 2. PR with head name equals
        domain = [
            ('repo_id', 'in', target_repo_ids),
            ('pull_head_name', '=', name),
            ('name', '=like', 'refs/pull/%'),
        ]
        pulls = branch_model.search_read(domain, fields, order='id DESC')
        pulls = sorted(pulls, key=sort_by_repo)
        for pull in pulls:
            pi = branch_model.browse(pull['id'])._get_pull_info()
            if pi.get('state') == 'open':
                return result_for(pull)

        # 3. Match a branch which is the dashed-prefix of current branch name
        branches = branch_model.search_read(
            [('repo_id', 'in', target_repo_ids), ('name', '=like', 'refs/heads/%')],
            fields + ['branch_name'], order='id DESC'
        )
        branches = sorted(branches, key=sort_by_repo)

        for branch in branches:
            if name.startswith(branch['branch_name'] + '-') and branch_exists(branch):
                return result_for(branch, 'prefix')

        # 4. Common ancestors (git merge-base)
        for target_id in target_repo_ids:
            common_refs = {}
            cr = self.env.cr
            cr.execute("""
                SELECT b.name
                  FROM runbot_branch b,
                       runbot_branch t
                 WHERE b.repo_id = %s
                   AND t.repo_id = %s
                   AND b.name = t.name
                   AND b.name LIKE 'refs/heads/%%'
            """, [repo.id, target_id])
            for common_name, in cr.fetchall():
                try:
                    commit = repo.git(['merge-base', branch['name'], common_name]).strip()
                    cmd = ['log', '-1', '--format=%cd', '--date=iso', commit]
                    common_refs[common_name] = repo.git(cmd).strip()
                except subprocess.CalledProcessError:
                    # If merge-base doesn't find any common ancestor, the command exits with a
                    # non-zero return code, resulting in subprocess.check_output raising this
                    # exception. We ignore this branch as there is no common ref between us.
                    continue
            if common_refs:
                b = sorted(common_refs.items(), key=operator.itemgetter(1), reverse=True)[0][0]
                return target_id, b, 'fuzzy'

        # 5. last-resort value
        return target_repo_id, 'master', 'default'

    def path(self, *l):
        self.ensure_one()
        root = self.env['runbot.repo'].root()
        return os.path.join(root, 'build', self.dest, *l)

    def server(self, *l):
        self.ensure_one()
        if os.path.exists(self.path('odoo')):
            return self.path('odoo', *l)
        return self.path('openerp', *l)

    def filter_modules(self, modules, available_modules, explicit_modules):
        blacklist_modules = set(['auth_ldap', 'document_ftp', 'base_gengo',
                                 'website_gengo', 'website_instantclick',
                                 'pos_cache', 'pos_blackbox_be'])

        mod_filter = lambda m: (
            m in available_modules and
            (m in explicit_modules or (not m.startswith(('hw_', 'theme_', 'l10n_'))
                                       and m not in blacklist_modules))
        )
        return uniq_list(filter(mod_filter, modules))

    def checkout(self):
        for build in self:
            # starts from scratch
            if os.path.isdir(build.path()):
                shutil.rmtree(build.path())

            # runbot log path
            mkdirs([build.path("logs"), build.server('addons')])

            # checkout branch
            build.repo_id.git_export(build.name, build.path())

            has_server = os.path.isfile(build.server('__init__.py'))
            server_match = 'builtin'

            # build complete set of modules to install
            modules_to_move = []
            modules_to_test = ((build.branch_id.modules or '') + ',' +
                               (build.repo_id.modules or ''))
            modules_to_test = list(filter(None, modules_to_test.split(',')))
            explicit_modules = set(modules_to_test)
            _logger.debug("manual modules_to_test for build %s: %s", build.dest, modules_to_test)

            if not has_server:
                if build.repo_id.modules_auto == 'repo':
                    modules_to_test += [
                        os.path.basename(os.path.dirname(a))
                        for a in glob.glob(build.path('*/__manifest__.py'))
                    ]
                    _logger.debug("local modules_to_test for build %s: %s", build.dest, modules_to_test)

                for extra_repo in build.repo_id.dependency_ids:
                    repo_id, closest_name, server_match = build._get_closest_branch_name(extra_repo.id)
                    repo = self.env['runbot.repo'].browse(repo_id)
                    _logger.debug('branch %s of %s: %s match branch %s of %s',
                                  build.branch_id.name, build.repo_id.name,
                                  server_match, closest_name, repo.name)
                    build._log(
                        'Building environment',
                        '%s match branch %s of %s' % (server_match, closest_name, repo.name)
                    )
                    repo.git_export(closest_name, build.path())

                # Finally mark all addons to move to openerp/addons
                modules_to_move += [
                    os.path.dirname(module)
                    for module in glob.glob(build.path('*/__manifest__.py'))
                ]

            # move all addons to server addons path
            for module in uniq_list(glob.glob(build.path('addons/*')) + modules_to_move):
                basename = os.path.basename(module)
                if os.path.exists(build.server('addons', basename)):
                    build._log(
                        'Building environment',
                        'You have duplicate modules in your branches "%s"' % basename
                    )
                    shutil.rmtree(build.server('addons', basename))
                shutil.move(module, build.server('addons'))

            available_modules = [
                os.path.basename(os.path.dirname(a))
                for a in glob.glob(build.server('addons/*/__manifest__.py'))
            ]
            if build.repo_id.modules_auto == 'all' or (build.repo_id.modules_auto != 'none' and has_server):
                modules_to_test += available_modules

            modules_to_test = self.filter_modules(modules_to_test, set(available_modules), explicit_modules)
            _logger.debug("modules_to_test for build %s: %s", build.dest, modules_to_test)
            build.write({
                'server_match': server_match,
                'modules': ','.join(modules_to_test)
            })

    def _local_pg_dropdb(self, dbname):
        with local_pgadmin_cursor() as local_cr:
            local_cr.execute('DROP DATABASE IF EXISTS "%s"' % dbname)
        # cleanup filestore
        datadir = appdirs.user_data_dir()
        paths = [os.path.join(datadir, pn, 'filestore', dbname) for pn in 'OpenERP Odoo'.split()]
        run(['rm', '-rf'] + paths)

    def _local_pg_createdb(self, dbname):
        self._local_pg_dropdb(dbname)
        _logger.debug("createdb %s", dbname)
        with local_pgadmin_cursor() as local_cr:
            local_cr.execute("""CREATE DATABASE "%s" TEMPLATE template0 LC_COLLATE 'C' ENCODING 'unicode'""" % dbname)

    def cmd(self):
        """Return a list describing the command to start the build"""
        self.ensure_one()
        build = self
        # Server
        server_path = build.path("odoo-bin")
        # for 10.0
        if not os.path.isfile(server_path):
            server_path = build.path("odoo.py")

        # commandline
        cmd = [
            sys.executable,
            server_path,
            "--xmlrpc-port=%d" % build.port,
            "--addons=%s" % build.server('addons'),
        ]
        # options
        if grep(build.server("tools/config.py"), "no-xmlrpcs"):
            cmd.append("--no-xmlrpcs")
        if grep(build.server("tools/config.py"), "no-netrpc"):
            cmd.append("--no-netrpc")
        if grep(build.server("tools/config.py"), "log-db"):
            logdb = self.env.cr.dbname
            if config['db_host'] and grep(build.server('sql_db.py'), 'allow_uri'):
                logdb = 'postgres://{cfg[db_user]}:{cfg[db_password]}@{cfg[db_host]}/{db}'.format(cfg=config, db=logdb)
            cmd += ["--log-db=%s" % logdb]

        if grep(build.server("tools/config.py"), "data-dir"):
            datadir = build.path('datadir')
            if not os.path.exists(datadir):
                os.mkdir(datadir)
            cmd += ["--data-dir", datadir]

        return cmd, build.modules

    def spawn(self, cmd, lock_path, log_path, cpu_limit=None, shell=False):
        def preexec_fn():
            os.setsid()
            if cpu_limit:
                # set soft cpulimit
                soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
                r = resource.getrusage(resource.RUSAGE_SELF)
                cpu_time = r.ru_utime + r.ru_stime
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_time + cpu_limit, hard))
            # close parent files
            os.closerange(3, os.sysconf("SC_OPEN_MAX"))
            lock(lock_path)

        out = open(log_path, "w")
        _logger.info("spawn: %s stdout: %s", ' '.join(cmd), log_path)
        p = subprocess.Popen(cmd, stdout=out, stderr=out, preexec_fn=preexec_fn, shell=shell)
        return p.pid

    def github_status(self):
        """Notify github of failed/successful builds"""
        runbot_domain = self.env['runbot.repo'].domain()
        for build in self:
            desc = "runbot build %s" % (build.dest,)
            if build.state == 'testing':
                state = 'pending'
            elif build.state in ('running', 'done'):
                state = 'error'
                if build.result == 'ok':
                    state = 'success'
                if build.result == 'ko':
                    state = 'failure'
                desc += " (runtime %ss)" % (build.job_time,)
            else:
                continue
            status = {
                "state": state,
                "target_url": "http://%s/runbot/build/%s" % (runbot_domain, build.id),
                "description": desc,
                "context": "ci/runbot"
            }
            _logger.debug("github updating status %s to %s", build.name, state)
            build.repo_id.github('/repos/:owner/:repo/statuses/%s' % build.name, status, ignore_errors=True)

    def job_00_init(self, build, lock_path, log_path):
        build._log('init', 'Init build environment')
        # notify pending build - avoid confusing users by saying nothing
        build.github_status()
        build.checkout()
        return -2

    def job_10_test_base(self, build, lock_path, log_path):
        build._log('test_base', 'Start test base module')
        # run base test
        self._local_pg_createdb("%s-base" % build.dest)
        cmd, mods = build.cmd()
        if grep(build.server("tools/config.py"), "test-enable"):
            cmd.append("--test-enable")
        cmd += ['-d', '%s-base' % build.dest, '-i', 'base', '--stop-after-init', '--log-level=test', '--max-cron-threads=0']
        return self.spawn(cmd, lock_path, log_path, cpu_limit=300)

    def job_20_test_all(self, build, lock_path, log_path):
        build._log('test_all', 'Start test all modules')
        self._local_pg_createdb("%s-all" % build.dest)
        cmd, mods = build.cmd()
        if grep(build.server("tools/config.py"), "test-enable"):
            cmd.append("--test-enable")
        cmd += ['-d', '%s-all' % build.dest, '-i', mods, '--stop-after-init', '--log-level=test', '--max-cron-threads=0']
        # reset job_start to an accurate job_20 job_time
        build.write({'job_start': fields.Datetime.now()})
        print(cmd)
        return self.spawn(cmd, lock_path, log_path, cpu_limit=2100)

    def job_30_run(self, build, lock_path, log_path):
        # adjust job_end to record an accurate job_20 job_time
        build._log('run', 'Start running build %s' % build.dest)
        log_all = build.path('logs', 'job_20_test_all.txt')
        log_time = time.localtime(os.path.getmtime(log_all))
        v = {
            'job_end': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT, log_time),
        }
        if grep(log_all, ".modules.loading: Modules loaded."):
            if rfind(log_all, _re_error):
                v['result'] = "ko"
            elif rfind(log_all, _re_warning):
                v['result'] = "warn"
            elif not grep(build.server("test/common.py"), "post_install") or grep(log_all, "Initiating shutdown."):
                v['result'] = "ok"
        else:
            v['result'] = "ko"
        build.write(v)
        build.github_status()

        # run server
        cmd, mods = build.cmd()
        if os.path.exists(build.server('addons/im_livechat')):
            cmd += ["--workers", "2"]
            cmd += ["--longpolling-port", "%d" % (build.port + 1)]
            cmd += ["--max-cron-threads", "1"]
        else:
            # not sure, to avoid old server to check other dbs
            cmd += ["--max-cron-threads", "0"]

        cmd += ['-d', "%s-all" % build.dest]

        if grep(build.server("tools/config.py"), "db-filter"):
            if build.repo_id.nginx:
                cmd += ['--db-filter', '%d.*$']
            else:
                cmd += ['--db-filter', '%s.*$' % build.dest]

        return self.spawn(cmd, lock_path, log_path, cpu_limit=None)

    def force(self):
        """Force a rebuild"""
        self.ensure_one()
        build = self
        domain = [('state', '=', 'pending')]
        sequence = self.search(domain, order='id', limit=1)
        if not sequence:
            sequence = self.search([], order='id desc', limit=1)

        # Force it now
        if build.state == 'done' and build.result == 'skipped':
            values = {'state': 'pending', 'sequence': sequence, 'result': ''}
            build.sudo().write(values)
        # or duplicate it
        elif build.state in ['running', 'done', 'duplicate']:
            new_build = {
                'sequence': sequence,
                'branch_id': build.branch_id.id,
                'name': build.name,
                'author': build.author,
                'author_email': build.author_email,
                'committer': build.committer,
                'committer_email': build.committer_email,
                'subject': build.subject,
                'modules': build.modules,
            }
            self.sudo().create(new_build)
        return build.repo_id.id

    def schedule(self):
        jobs = self.list_jobs()

        icp = self.env['ir.config_parameter']
        # For retro-compatibility, keep this parameter in seconds
        default_timeout = int(icp.get_param('runbot.timeout', default=1800)) / 60

        for build in self:
            if build.state == 'pending':
                # allocate port and schedule first job
                port = self.find_port()
                values = {
                    'host': fqdn(),
                    'port': port,
                    'state': 'testing',
                    'job': jobs[0],
                    'job_start': fields.Datetime.now(),
                    'job_end': False,
                }
                build.write(values)
                self._cr.commit()
            else:
                # check if current job is finished
                lock_path = build.path('logs', '%s.lock' % build.job)
                if locked(lock_path):
                    # kill if overpassed
                    timeout = (build.branch_id.job_timeout or default_timeout) * 60
                    if build.job != jobs[-1] and build.job_time > timeout:
                        build.logger('%s time exceded (%ss)', build.job, build.job_time)
                        build.write({'job_end': fields.Datetime.now()})
                        build.kill(result='killed')
                    continue
                build.logger('%s finished', build.job)
                # schedule
                v = {}
                # testing -> running
                if build.job == jobs[-2]:
                    v['state'] = 'running'
                    v['job'] = jobs[-1]
                    v['job_end'] = fields.Datetime.now(),
                # running -> done
                elif build.job == jobs[-1]:
                    v['state'] = 'done'
                    v['job'] = ''
                # testing
                else:
                    v['job'] = jobs[jobs.index(build.job) + 1]
                build.write(v)
            build.refresh()

            # run job
            pid = None
            if build.state != 'done':
                build.logger('running %s', build.job)
                job_method = getattr(self, build.job)
                mkdirs([build.path('logs')])
                lock_path = build.path('logs', '%s.lock' % build.job)
                log_path = build.path('logs', '%s.txt' % build.job)
                pid = job_method(build, lock_path, log_path)
                build.write({'pid': pid})
            # needed to prevent losing pids if multiple jobs are started and one them raise an exception
            self._cr.commit()

            if pid == -2:
                # no process to wait, directly call next job
                # FIXME find a better way that this recursive call
                build.schedule()

            # cleanup only needed if it was not killed
            if build.state == 'done':
                build._local_cleanup()

    def skip(self):
        self.write({'state': 'done', 'result': 'skipped'})
        to_unduplicate = self.search([('id', 'in', self.ids), ('duplicate_id', '!=', False)])
        for b in to_unduplicate:
            b.force()

    def _local_cleanup(self):
        for build in self:
            # Cleanup the *local* cluster
            with local_pgadmin_cursor() as local_cr:
                local_cr.execute("""
                    SELECT datname
                      FROM pg_database
                     WHERE pg_get_userbyid(datdba) = current_user
                       AND datname LIKE %s
                """, [build.dest + '%'])
                to_delete = local_cr.fetchall()
            for db, in to_delete:
                self._local_pg_dropdb(db)

        # cleanup: find any build older than 7 days.
        root = self.env['runbot.repo'].root()
        build_dir = os.path.join(root, 'build')
        builds = os.listdir(build_dir)
        self._cr.execute("""
            SELECT dest
              FROM runbot_build
             WHERE dest IN %s
               AND (state != 'done' OR job_end > (now() - interval '7 days'))
        """, [tuple(builds)])
        actives = set(b[0] for b in self._cr.fetchall())

        for b in builds:
            path = os.path.join(build_dir, b)
            if b not in actives and os.path.isdir(path):
                shutil.rmtree(path)

    def kill(self, result=None):
        for build in self:
            build._log('kill', 'Kill build %s' % build.dest)
            build.logger('killing %s', build.pid)
            try:
                os.killpg(build.pid, signal.SIGKILL)
            except OSError:
                pass
            v = {'state': 'done', 'job': False}
            if result:
                v['result'] = result
            build.write(v)
            self._cr.commit()
            build.github_status()
            build._local_cleanup()

    def reap(self):
        while True:
            try:
                pid, status, rusage = os.wait3(os.WNOHANG)
            except OSError:
                break
            if pid == 0:
                break
            _logger.debug('reaping: pid: %s status: %s', pid, status)

    def _log(self, func, message):
        self.ensure_one()
        _logger.debug("Build %s %s %s", self.id, func, message)
        self.env['ir.logging'].create({
            'build_id': self.id,
            'level': 'INFO',
            'type': 'runbot',
            'name': 'odoo.runbot',
            'message': message,
            'path': 'runbot',
            'func': func,
            'line': '0',
        })
