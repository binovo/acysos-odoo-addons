# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# (c) 2017 Diagram Software S.L.
# Copyright (c) 2017-TODAY MINORISA <ramon.guiu@minorisa.net>
# (c) 2017 Studio73 - Pablo Fuentes <pablo@studio73.es>
# (c) 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Suministro Inmediato de Información en el IVA",
    "version": "8.0.1.2.5",
    "category": "Accounting & Finance",
    "website": "https://www.acysos.com",
    "author": "Acysos S.L.",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ["zeep",
                   "requests"],
    },
    "depends": [
        "account_refund_original",
        "l10n_es_aeat",
        "connector",
        "account_payment_partner",
        "account_chart_update"
    ],
    "data": [
        "data/ir_config_parameter.xml",
        "views/res_company_view.xml",
        "views/account_invoice_view.xml",
        "views/aeat_sii_view.xml",
        "views/aeat_sii_result_view.xml",
        "views/aeat_check_sii_result_view.xml",
        "wizard/aeat_sii_password_view.xml",
        "views/aeat_sii_mapping_registration_keys_view.xml",
        "data/aeat_sii_mapping_registration_keys_data.xml",
        "views/aeat_sii_map_view.xml",
        "data/aeat_sii_map_data.xml",
        "data/aeat_sii_map_data_1_1.xml",
        "data/aeat_sii_mapping_payment_keys_data.xml",
        "security/ir.model.access.csv",
        "security/aeat_sii.xml",
        "views/product_view.xml",
        "views/account_view.xml",
        "views/account_payment_mode_view.xml",
        "data/account_fiscal_position_data.xml"
    ],
    'images': ['static/description/banner.jpg'],
    "post_init_hook": "post_init_sii_hook",
}
