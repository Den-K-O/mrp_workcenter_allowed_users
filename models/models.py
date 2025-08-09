# Copyright 2022 ForgeFlow S.L.
#   (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
from odoo.exceptions import UserError


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    allowed_user_ids = fields.Many2many(
        comodel_name="res.users",
        string="Users",
    )


class MrpWorkOrder(models.Model):
    _inherit = "mrp.workorder"

    def button_start(self):
        if self.env.user not in self.workcenter_id.allowed_user_ids:
            raise UserError("Немає доступу до робочого центру")
            return
        super().button_start()

    def button_finish(self):
        if self.env.user not in self.workcenter_id.allowed_user_ids:
            raise UserError("Немає доступу до робочого центру")
            return
        super().button_finish()

    def button_pending(self):
        if self.env.user not in self.workcenter_id.allowed_user_ids:
            raise UserError("Немає доступу до робочого центру")
            return
        super().button_pending()
    
    def button_unblock(self):
        if self.env.user not in self.workcenter_id.allowed_user_ids:
            raise UserError("Немає доступу до робочого центру")
            return
        super().button_unblock()


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            workcenter_id = vals.get("workcenter_id")
            if workcenter_id:
                workcenter = self.env['mrp.workcenter'].browse(workcenter_id)
                if self.env.user not in workcenter.allowed_user_ids:
                    raise UserError("Немає доступу до блокування робочого центру")
        return super().create(vals_list)

    def button_block(self):
        self.ensure_one()
        if self.env.user not in self.workcenter_id.allowed_user_ids:
            # Optional: clean up the wizard record
            self.unlink()
            raise UserError("Немає доступу до блокування робочого центру")
        
        # Continue with the normal behavior
        self.workcenter_id.order_ids.end_all()