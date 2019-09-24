# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from enum import Enum
from openerp.tests import common
from openerp import exceptions, api
from datetime import datetime
from openerp.addons.l10n_es_aeat_sii.models.account_invoice import AccountInvoice as AI

AI.l10n_es_aeat_sii_test_send_soap = AI._send_soap


class ResponseType(Enum):
    correct = 'correct'
    incorrect = 'incorrect'
    exception = 'exception'


SII_RESPONSES = {
    ResponseType.correct.value: {
        'EstadoEnvio': 'Correcto',
        'CSV': 'TEST-CORRECT-CSV',
        'RespuestaLinea': [{
            'CodigoErrorRegistro': None
        }]
    },
    ResponseType.incorrect.value: {
        'EstadoEnvio': 'Incorrecto',
        'RespuestaLinea': [{
            'CodigoErrorRegistro': 1111111,
            'DescripcionErrorRegistro': 'Test incorrect response - DescripcionErrorRegistro'
        }]
    },
    ResponseType.exception.value: {}
}


@api.multi
def _send_soap(self, wsdl, port_name, operation, param1, param2):
    self.ensure_one()
    sii_response_type_by_invoice_id = self._context.get('sii_response_type_by_invoice_id', False)
    if sii_response_type_by_invoice_id is False:
        return self.l10n_es_aeat_sii_test_send_soap(wsdl, port_name, operation, param1, param2)
    return SII_RESPONSES[sii_response_type_by_invoice_id[self.id]]


AI._send_soap = _send_soap


def _deep_sort(obj):
    """
    Recursively sort list or dict nested lists
    """
    if isinstance(obj, dict):
        _sorted = {}
        for key in sorted(obj):
            _sorted[key] = _deep_sort(obj[key])
    elif isinstance(obj, list):
        new_list = []
        for val in obj:
            new_list.append(_deep_sort(val))
        _sorted = sorted(new_list)
    else:
        _sorted = obj
    return _sorted


class TestL10nEsAeatSii(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsAeatSii, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'vat': 'ESF35999705',
            'is_company': True,
            'state_id': self.env.ref('l10n_es_toponyms.ES20').id,
            'city': 'Oiartzun',
            'country_id': self.env.ref('base.es').id,
            'zip': 20180
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
        })
        self.account_type = self.env['account.account.type'].create({
            'name': 'Test account type',
            'code': 'TEST',
        })
        self.account_expense = self.env['account.account'].create({
            'name': 'Test expense account',
            'code': 'EXP',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Test analytic account',
            'type': 'normal',
        })
        self.account_tax = self.env['account.account'].create({
            'name': 'Test tax account',
            'code': 'TAX',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.base_code = self.env['account.tax.code'].create({
            'name': '[28] Test base code',
            'code': 'OICBI',
        })
        self.tax_code = self.env['account.tax.code'].create({
            'name': '[29] Test tax code',
            'code': 'SOICC',
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test tax 10%',
            'type_tax_use': 'purchase',
            'type': 'percent',
            'amount': '0.10',
            'account_collected_id': self.account_tax.id,
            'base_code_id': self.base_code.id,
            'base_sign': 1,
            'tax_code_id': self.tax_code.id,
            'tax_sign': 1,
        })
        self.period = self.env['account.period'].find()
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'fiscal_position': self.env.ref('l10n_es.fp_nacional').id,
            'registration_key': self.env.ref('l10n_es_aeat_sii.aeat_sii_mapping_registration_keys_01').id,
            'period_id': self.period.id,
            'account_id': self.partner.property_account_payable.id,
            'invoice_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'account_analytic_id': self.analytic_account.id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_id': [(6, 0, [self.env.ref('l10n_es.account_tax_template_p_iva10_bc').id])],
                })]
        })

    def _open_invoice(self):
        self.invoice.company_id.write({
            'sii_enabled': True,
            'use_connector': True,
            'chart_template_id': self.env.ref(
                'l10n_es.account_chart_template_pymes').id,
            'vat': 'ESU2687761C',
        })
        self.invoice.signal_workflow('invoice_open')

    def test_job_creation(self):
        self._open_invoice()
        self.assertTrue(self.invoice.invoice_jobs_ids)

    def _get_invoices_test(self, invoice_type, special_regime):
        str_today = datetime.now().strftime("%d-%m-%Y")
        emisor = self.invoice.company_id
        contraparte = self.partner
        expedida_recibida = 'FacturaExpedida'
        if self.invoice.type in ['in_invoice', 'in_refund']:
            emisor = self.partner
            expedida_recibida = 'FacturaRecibida'
        res = {
            'IDFactura': {
                'FechaExpedicionFacturaEmisor': str_today,
                'IDEmisorFactura': {
                    'NIF': emisor.vat[2:]},
                'NumSerieFacturaEmisor': (
                    self.invoice.supplier_invoice_number or
                    self.invoice.number)},
            expedida_recibida: {
                'TipoFactura': invoice_type,
                'Contraparte': {
                    'NombreRazon': contraparte.name,
                    'NIF': contraparte.vat[2:],
                },
                'DescripcionOperacion': u'/',
                'ClaveRegimenEspecialOTrascendencia': special_regime,
            },
            'PeriodoLiquidacion': {
                'Periodo': str(self.invoice.period_id.code[:2]),
                'Ejercicio': int(self.invoice.period_id.code[-4:])
            }
        }
        if self.invoice.type in ['out_invoice', 'out_refund']:
            res[expedida_recibida].update({
                'TipoDesglose': {},
                'ImporteTotal': self.invoice.amount_total,
            })
        else:
            res[expedida_recibida].update({
                "FechaRegContable":
                    datetime.strptime(
                        self.invoice.date_invoice,
                        '%Y-%m-%d').strftime('%d-%m-%Y'),
                "DesgloseFactura": {
                    'DesgloseIVA': {
                        'DetalleIVA': [{
                            'BaseImponible': self.invoice.invoice_line.price_unit,
                            'CuotaSoportada': self.invoice.invoice_line.invoice_line_tax_id.amount * 100,
                            'TipoImpositivo': self.invoice.invoice_line.invoice_line_tax_id.amount * 100
                        }]
                    }
                },
                "CuotaDeducible": self.invoice.amount_tax,
                'ImporteTotal': self.invoice.amount_total
            })
        if invoice_type == 'R4':
            invoices = self.invoice.origin_invoices_ids
            base_rectificada = sum(invoices.mapped('amount_untaxed'))
            cuota_rectificada = sum(invoices.mapped('amount_tax'))
            res[expedida_recibida].update({
                'TipoRectificativa': 'S',
                'ImporteRectificacion': {
                    'BaseRectificada': base_rectificada,
                    'CuotaRectificada': cuota_rectificada,
                }
            })
        return res

    def test_get_invoice_data(self):
        self._open_invoice()

        vat = self.partner.vat
        self.partner.vat = False
        with self.assertRaises(exceptions.Warning):
            self.invoice._get_invoices()
        self.partner.vat = vat

        invoices = self.invoice._get_invoices()
        test_out_inv = self._get_invoices_test('F1', u'01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_out_inv.get(key)))

        self.invoice.type = 'out_refund'
        self.invoice.refund_type = 'S'
        invoices = self.invoice._get_invoices()
        test_out_refund = self._get_invoices_test('R4', u'01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_out_refund.get(key)))

        self.invoice.type = 'in_invoice'
        self.invoice.supplier_invoice_number = 'sup0001'
        invoices = self.invoice._get_invoices()
        test_in_invoice = self._get_invoices_test('F1', u'01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_in_invoice.get(key)))

        self.invoice.type = 'in_refund'
        self.invoice.refund_type = 'S'
        self.invoice.supplier_invoice_number = 'sup0001'
        invoices = self.invoice._get_invoices()
        test_in_refund = self._get_invoices_test('R4', u'01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_in_refund.get(key)))

    def test_action_cancel(self):
        self._open_invoice()
        self.invoice.invoice_jobs_ids.state = 'started'
        self.invoice.journal_id.update_posted = True
        with self.assertRaises(exceptions.Warning):
            self.invoice.action_cancel()

    def test_00_send_multiple_invoices(self):
        """
        To test:
        1. send multiple invoices, one of them should return an error/exception (check both)
        """
        self.invoice.company_id.write({
            'sii_enabled': True,
            'use_connector': False,
            'sii_method': 'manual',
            'chart_template_id': self.env.ref(
                'l10n_es.account_chart_template_pymes').id,
            'vat': 'ESU2687761C',
        })
        invoice1 = self.invoice
        invoice2 = self.invoice.copy()
        invoice3 = self.invoice.copy()
        invoice1.signal_workflow('invoice_open')
        invoice2.signal_workflow('invoice_open')
        invoice3.signal_workflow('invoice_open')

        invoices = self.env['account.invoice']
        invoices |= invoice1
        invoices |= invoice2
        invoices |= invoice3

        invoices.with_context(sii_response_type_by_invoice_id={
            invoice1.id: ResponseType.correct.value,
            invoice2.id: ResponseType.incorrect.value,
            invoice3.id: ResponseType.exception.value
        }).send_sii()
        self.assertTrue(invoice1.sii_sent)
        self.assertEqual(1, len(invoice1.sii_results))
        self.assertEqual('Correcto', invoice1.sii_results.sent_state)
        self.assertFalse(invoice2.sii_sent)
        self.assertEqual(1, len(invoice2.sii_results))
        self.assertEqual('Incorrecto', invoice2.sii_results.sent_state)
        self.assertFalse(invoice3.sii_sent)
        self.assertEqual(1, len(invoice3.sii_results))
        self.assertEqual(False, invoice3.sii_results.sent_state)
