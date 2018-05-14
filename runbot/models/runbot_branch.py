import re
import subprocess

from odoo import models, fields, api


class RunbotBranch(models.Model):
    _name = "runbot.branch"
    _order = 'name'

    repo_id = fields.Many2one('runbot.repo', 'Repository', required=True, ondelete='cascade')
    name = fields.Char('Ref Name', required=True)
    branch_name = fields.Char(compute='_compute_branch_name_url', string='Branch', store=True)
    branch_url = fields.Char(compute='_compute_branch_name_url', string='Branch url')
    pull_head_name = fields.Char(compute='_compute_pull_head_name', string='PR HEAD name', readonly=1, store=True)
    sticky = fields.Boolean('Sticky')
    coverage = fields.Boolean('Coverage')
    state = fields.Char('Status')
    modules = fields.Char("Modules to Install", help="Comma-separated list of modules to install and test.")
    job_timeout = fields.Integer('Job Timeout (minutes)', help='For default timeout: Mark it zero')

    @api.depends('repo_id', 'name')
    def _compute_branch_name_url(self):
        for r in self:
            b_name = r.branch_name = r.name.split('/')[-1]
            if re.match('^[0-9]+$', b_name):
                r.branch_url = "https://%s/pull/%s" % (r.repo_id.base, r.branch_name)
            else:
                r.branch_url = "https://%s/tree/%s" % (r.repo_id.base, r.branch_name)

    @api.depends()
    def _compute_pull_head_name(self):
        for r in self:
            pi = r._get_pull_info()
            if pi:
                r.pull_info = pi['head']['ref']

    def _get_pull_info(self):
        self.ensure_one()
        repo = self.repo_id
        if repo.token and self.name.startswith('refs/pull/'):
            pull_number = self.name[len('refs/pull/'):]
            return repo.github('/repos/:owner/:repo/pulls/%s' % pull_number, ignore_errors=True) or {}
        return {}

    def _is_on_remote(self):
        # check that a branch still exists on remote
        self.ensure_one()
        repo = self.repo_id
        try:
            repo.git(['ls-remote', '-q', '--exit-code', repo.name, self.name])
        except subprocess.CalledProcessError:
            return False
        return True
