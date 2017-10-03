# -*- coding: utf-8 -*-
# Copyright 2017 Onestein (<http://www.onestein.eu>)
# Copyright 2017 Alex Comba - Agile Business Group
# Copyright 2017 Nicola Malcontenti - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class OdooModule(models.Model):
    _inherit = 'odoo.module'

    product_template_id = fields.Many2one(
        'product.template', string="Product Template")

    @api.multi
    def action_create_product(self):
        self._create_product()

    @api.multi
    def _create_product(self):
        for module in self:
            if module.product_template_id:
                continue
            matching_template = self.env['product.template'].search(
                [('odoo_module_id', '=', module.id)], limit=1)
            if matching_template:
                module.product_template_id = matching_template
                continue
            template_dict = module._get_template_values()
            new_template = self.env['product.template'].create(template_dict)
            module.product_template_id = new_template

    @api.multi
    def _get_template_values(self):
        self.ensure_one()

        milestones = self.module_version_ids.mapped(
            'repository_branch_id').mapped(
                'organization_milestone_id').mapped('name')
        value_ids = self.env['product.attribute.value'].search(
            [('name', 'in', milestones)]).ids

        res = {
            'odoo_module_id': self.id,
            'type': 'service',
            'name': self.name,
            'image': self.image,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': self.env.ref(
                    'apps_product_creator.attribute_odoo_version').id,
                'value_ids': [(6, 0, value_ids)],
            })]
        }
        return res

    @api.model
    def cron_create_product(self):
        modules = self.search([('product_template_id', '=', False),
                               ('module_version_qty', '!=', 0)])
        modules.action_create_product()
        return True

    @api.multi
    def write(self, vals):
        to_update = False
        if vals.get('image', False):
            to_update = True
        ret = super(OdooModule, self).write(vals)
        if to_update:
            for module in self.filtered(lambda x: x.product_template_id):
                module.product_template_id.image = module.image
        return ret