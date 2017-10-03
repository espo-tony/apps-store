# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today: Odoo Community Association (OCA)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo import tools


class ProductProduct(models.Model):
    _inherit = 'product.product'

    odoo_module_version_id = fields.Many2one(
        'odoo.module.version',
        'Odoo Module',
    )
    license = fields.Char(
        'License (Manifest)',
        readonly=True,
        related="odoo_module_version_id.license",
        store=True,
    )
    summary = fields.Char(
        'Summary (Manifest)',
        readonly=True,
        related="odoo_module_version_id.summary",
        store=True,
    )
    website = fields.Char(
        'Website (Manifest)',
        readonly=True,
        related="odoo_module_version_id.website",
        store=True,
    )
    external_dependencies = fields.Char(
        'External Dependencies (Manifest)',
        readonly=True,
        related="odoo_module_version_id.external_dependencies",
        store=True,
    )
    description_rst = fields.Char(
        'RST Description (Manifest)',
        readonly=True,
        related="odoo_module_version_id.description_rst",
        store=True,
    )
    description_rst_html = fields.Html(
        'HTML the RST Description',
        readonly=True,
        related="odoo_module_version_id.description_rst_html",
        store=True,
    )
    version = fields.Char(
        'Version (Manifest)',
        readonly=True,
        related="odoo_module_version_id.version",
        store=True,
    )
    author = fields.Char(
        'Author (Manifest)',
        readonly=True,
        related="odoo_module_version_id.author",
        store=True,
    )
    image = fields.Binary(
        'Icon Image',
        reaonly=True,
        related="odoo_module_version_id.image",
        store=True,
    )
    github_url = fields.Char(
        'Github URL',
        readonly=True,
        related="odoo_module_version_id.github_url",
        store=True,
    )
    image = fields.Binary(
        "Big-sized image",
        compute='_compute_images',
        inverse='_set_image',
        help="Image of the product variant (Big-sized image of product "
             "template if false). It is automatically resized as a "
             "1024x1024px image, with aspect ratio preserved.",
    )
    image_small = fields.Binary(
        "Small-sized image",
        compute='_compute_images',
        inverse='_set_image_small',
        help="Image of the product variant (Small-sized image of "
             "product template if false).",
    )
    image_medium = fields.Binary(
        "Medium-sized image",
        compute='_compute_images',
        inverse='_set_image_medium',
        help="Image of the product variant (Medium-sized image of "
             "product template if false).",
    )

    @api.model
    def create(self, values):
        """
        Apply the behaviour to product used to save modules.
        :param values: dict
        :return: self recordset
        """
        self._manage_product_module(values)
        return super(ProductProduct, self).create(values)

    @api.model
    def _manage_product_module(self, values):
        """
        Manage product variants related to modules.
        During the creation of a new product.product (who is a variant), we
        check if the product is used to save a module (by the odoo_module_id
        field).
        Then check into given variant attributes if we find the variant used
        to save the module version (with XML ID:
        github_product_creator.attribute_odoo_version).
        If it's the case, we check the version (based on the attribute value)
        and just link the product.product to this version
        :param values: dict
        :return: bool
        """
        product_tmpl_key = "product_tmpl_id"
        attr_key = "attribute_value_ids"
        check_keys = [
            product_tmpl_key,
            attr_key,
        ]
        values_keys = values.keys()
        # Check if mandatory keys (for product module) are given
        if all([k in values_keys for k in check_keys]):
            product_obj = self.env['product.template']
            product = product_obj.browse(values.get(product_tmpl_key, []))
            # If the product template is used to save an Odoo module
            if self._check_related_to_module(product):
                attribute = self._get_version_attribute(values)
                version = self._get_version_with_attribute(product.odoo_module_id.module_version_ids, attribute)
                # If we don't have a result, the ID will be False
                values.update({
                    'odoo_module_version_id': version.id,
                })
        return True

    @api.model
    def _get_version_with_attribute(self, versions, attribute):
        """
        Get the version recordset (odoo.module.version) into the given version
        (versions) based on the attribute name.
        :param versions: odoo.module.version recordset
        :param attribute: product.attribute.value recordset
        :return: odoo.module.version recordset
        """
        # Attribute value (so the name field) must be the milestone name
        # (so the version). So we can compare name without managing
        # translations.
        version = versions.filtered(
            lambda x: x.organization_milestone_id.name == attribute.name)
        return version

    @api.model
    def _check_related_to_module(self, product):
        """
        Check if the product template is related to a module or not
        :param product: product.template recordset
        :return: bool
        """
        return bool(product.odoo_module_id)

    @api.model
    def _get_version_attribute(self, values):
        """
        Get the attribute value used to save the Module version (using the
        xml id) if it's into the given dict values.
        :param values: dict
        :return: product.attribute.value recordset (0 or 1 recordset)
        """
        attr_obj = self.env['product.attribute.value']
        attr_xml_id = "github_product_creator.attribute_odoo_version"
        attr_key = "attribute_value_ids"
        version_attribute = self.env.ref(attr_xml_id)
        attr_raw_ids = values.get(attr_key, [])
        attr_ids = []
        # The MAGIC NUMBER used to create variants are (6, _, list) so we must
        # have the last element of the tuple
        if attr_raw_ids and len(attr_raw_ids[0]) > 1:
            attr_ids = attr_raw_ids[0][2]
        attributes = attr_obj.browse(attr_ids)
        # We should have 0 or 1 result maximum. Because we compare id.
        attribute = attributes.filtered(
            lambda a: a.attribute_id.id == version_attribute.id)
        return attribute

    @api.multi
    @api.depends('image_variant', 'product_tmpl_id.image', 'image_module',
                 'odoo_module_version_id')
    def _compute_images(self):
        products = self.filtered(
            lambda p: p.odoo_module_version_id and p.image_module)
        other_products = self.filtered(lambda p: p not in products)
        for product in products:
            if self._context.get('bin_size'):
                product.image_medium = product.image_module
                product.image_small = product.image_module
                product.image = product.image_module
            else:
                resized_images = tools.image_get_resized_images(
                    product.image_module, return_big=True,
                    avoid_resize_medium=True)
                product.image_medium = resized_images.get('image_medium')
                product.image_small = resized_images.get('image_small')
                product.image = resized_images.get('image')
            if not product.image_medium:
                product.image_medium = product.product_tmpl_id.image_medium
            if not product.image_small:
                product.image_small = product.product_tmpl_id.image_small
            if not product.image:
                product.image = product.product_tmpl_id.image
        super(ProductProduct, other_products)._compute_images()
