# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    estructura_id = fields.Many2one('hr.payroll.structure','Estructura')

    @api.multi
    def compute_sheet(self):
        datos_anteriores = []
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        estructura = self.estructura_id
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            if estructura:
                slip_data_anterior = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
                contrato_id= self.env['hr.contract'].search([('id','=',slip_data_anterior['value'].get('contract_id'))])
                estructura_anterior = contrato_id.struct_id
                datos_anteriores.append({'empleado': employee,'contrato': contrato_id,'estructura_anterior': estructura_anterior})
                contrato_id.struct_id = estructura.id

            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': estructura.id if estructura else slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()

        if estructura and datos_anteriores:
            for dato in datos_anteriores:
                dato['contrato'].struct_id = dato['estructura_anterior'].id

        return {'type': 'ir.actions.act_window_close'}
