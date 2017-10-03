# -*- coding: utf-8 -*-

import os
import tempfile
import shutil
import logging
import base64
import subprocess
from odoo.exceptions import ValidationError
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    dependent_product_ids = fields.Many2many('product.product', 'prto_validateoduct_dependent_rel', 'src_id', 'dest_id', string='Dependent Products')
    module_path = fields.Char('Module Path')

    @api.constrains('dependent_product_ids')
    def check_dependent_recursion(self):
        for product in self:
            def child_dependancy_check(product_dependent_ids, children):
                res = self.env['product.product']
                for child in children:
                    if not child.dependent_product_ids:
                        continue
                    if child in product_dependent_ids:
                        raise ValidationError(_('Error ! You cannot create recursive Dependency.'))
                    product_dependent_ids += child
                    child_dependancy_check(product_dependent_ids, child.dependent_product_ids)
                return res

            child_dependancy_check(product, product.dependent_product_ids)

    @api.multi
    def create_dependency_list(self):
        ret_val = {}
        def child_dependency(children):
            res = self.env['product.product']
            for child in children:
                if not child.dependent_product_ids:
                    continue
                res += child.dependent_product_ids
                res += child_dependency(child.dependent_product_ids)
            return res
        for product in self:
            ret_val[product.id] = product.dependent_product_ids
            if product.dependent_product_ids:
                ret_val[product.id] += child_dependency(product.dependent_product_ids)
        return ret_val

    @api.multi
    def generate_zip_file(self):
        for product in self:
            if not product.module_path:
                continue
            tmpdir = tempfile.mkdtemp()
            tmpdir2 = tempfile.mkdtemp()
            dependent_product_ids = product.create_dependency_list()[product.id]
            for dependent_product in dependent_product_ids:
                if not dependent_product.module_path:
                    continue
                print "3333333#",dependent_product.module_path
                p1 = subprocess.Popen(['cp','-r', dependent_product.module_path, tmpdir], stdout=subprocess.PIPE)
            p1 = subprocess.Popen(['cp','-r', product.module_path, tmpdir], stdout=subprocess.PIPE)
            #createzip of folder
            tmpzipfile = os.path.join(tmpdir2,product.name)
            shutil.make_archive(tmpzipfile, 'zip', tmpdir)
            tmpzipfile = tmpzipfile + '.zip'
            with open(tmpzipfile, "rb") as fileobj:
                try:
                    data_encode = base64.encodestring(fileobj.read())
                    self.env['ir.attachment'].create({
                        'datas': data_encode,
                        'datas_fname': tmpzipfile,
                        'type': 'binary',
                        'name': product.name + '.zip',
                        'res_model': product._name,
                        'res_id': product.id,
                        'product_downloadable': True,
                    })
                except:
                    _logger.error('Error creating attachment %s' % tmpzipfile)
            try:
                shutil.rmtree(tmpdir)
                shutil.rmtree(tmpdir2)
            except Exception as exc:
                _logger.warning('Could not remove Tempdir %s, Errormsg %s' % (tmpdir, exc.message))

    @api.model
    def generate_zip_file_batch(self):
        self.search([]).generate_zip_file()

ProductProduct()
