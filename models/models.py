# Copyright 2022 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
from odoo.exceptions import UserError
from lxml import etree


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    allowed_user_ids = fields.Many2many(
        comodel_name="res.users",
        string="Users",
    )


class MrpWorkOrder(models.Model):
    _inherit = "mrp.workorder"

    allowed_user_ids = fields.Many2many(
        'res.users',
        related='workcenter_id.allowed_user_ids',
        readonly=True,
    )

    worker = fields.Many2one(
        "res.users",
        "Worker", 
    )

    def button_start(self):
        if self.workcenter_id and self.env.user not in self.workcenter_id.allowed_user_ids:
            raise UserError(f"Немає доступу до робочого центру {self.workcenter_id.name}: button_start")
            return
        super().button_start()

    def button_finish(self):
        if self.workcenter_id and self.env.user not in self.workcenter_id.allowed_user_ids:
            raise UserError(f"Немає доступу до робочого центру {self.workcenter_id.name}: button_finish")
            return
        super().button_finish()

    def button_pending(self):
        if self.workcenter_id and self.env.user not in self.workcenter_id.allowed_user_ids:
            raise UserError(f"Немає доступу до робочого центру {self.workcenter_id.name}: button_pending")
            return
        super().button_pending()
    
    def button_unblock(self):
        if self.workcenter_id and self.env.user not in self.workcenter_id.allowed_user_ids:
            raise UserError(f"Немає доступу до робочого центру {self.workcenter_id.name}: button_unblock")
            return
        super().button_unblock()
    
    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super()._fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type not in ('tree', 'form'):
            return res

        user = self.env.user
        is_manager = user.has_group('mrp.group_mrp_manager')

        doc = etree.XML(res['arch'])

        for node in doc.xpath("//field[@class='worker_main']"):

            if is_manager:
                # Managers: full access
                node.set('domain', "[('id', 'in', allowed_user_ids)]")

            else:
                # Employees: only self
                node.set('domain', "[('id', '=', uid), ('id', 'in', allowed_user_ids)]")

                # Readonly if already set to another user, or the current user is not in the allowed users list
                node.set(
                    'attrs', str({
                         'readonly': [
                            '|',
                            # Case A: already set to another user
                            '&',
                            ('worker', '!=', False),
                            ('worker', '!=', user.id),

                            # Case B: empty but user not allowed
                            '&',
                            ('worker', '=', False),
                            ('allowed_user_ids', 'not in', [user.id]),
                        ]
                    })
                )
        
        for node in doc.xpath("//field[@name='workcenter_id']"):
            if not is_manager:
                node.set(
                        'attrs', str({
                            'readonly': True
                        })
                    )
        
        for node in doc.xpath("//field[@name='name']"):
            if not is_manager:
                node.set(
                        'attrs', str({
                            'readonly': True
                        })
                    )

        res['arch'] = etree.tostring(doc, encoding='unicode')
        print(res['arch'])
        return res


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            workcenter_id = vals.get("workcenter_id")
            if workcenter_id:
                workcenter = self.env['mrp.workcenter'].browse(workcenter_id)
                if workcenter and self.env.user not in workcenter.allowed_user_ids:
                    raise UserError(f"Немає доступу до блокування робочого центру {workcenter.name}: create")
        return super().create(vals_list)

    def button_block(self):
        self.ensure_one()
        if self.workcenter_id and self.env.user not in self.workcenter_id.allowed_user_ids:
            # Optional: clean up the wizard record
            self.unlink()
            raise UserError(f"Немає доступу до блокування робочого центру {self.workcenter_id.name}: button_block")
        
        # Continue with the normal behavior
        self.workcenter_id.order_ids.end_all()


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super()._fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type not in ('tree', 'form'):
            return res

        user = self.env.user
        is_manager = user.has_group('mrp.group_mrp_manager')

        doc = etree.XML(res['arch'])

        for node in doc.xpath("//field[@name='workorder_ids']"):
            if not is_manager:
                node.set(
                        'attrs', str({
                            'readonly': True
                        })
                    )

        res['arch'] = etree.tostring(doc, encoding='unicode')
        print(res['arch'])
        return res