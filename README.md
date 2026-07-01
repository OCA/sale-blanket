
[![Support the OCA](https://odoo-community.org/readme-banner-image)](https://odoo-community.org/get-involved?utm_source=repo-readme)

# sale-blanket
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/sale-blanket&target_branch=18.0)
[![Pre-commit Status](https://github.com/OCA/sale-blanket/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/OCA/sale-blanket/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/OCA/sale-blanket/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/OCA/sale-blanket/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/OCA/sale-blanket/branch/18.0/graph/badge.svg)](https://codecov.io/gh/OCA/sale-blanket)
[![Translation Status](https://translation.odoo-community.org/widgets/sale-blanket-18-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/sale-blanket-18-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

sale-blanket

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[sale_blanket_order](sale_blanket_order/) | 18.0.1.2.2 |  | Blanket Orders
[sale_order_blanket_order](sale_order_blanket_order/) | 18.0.1.0.4 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> <a href='https://github.com/lmignon'><img src='https://github.com/lmignon.png' width='32' height='32' style='border-radius:50%;' alt='lmignon'/></a> | Manage blanket order and call of order
[sale_order_blanket_order_carrier_auto_assign](sale_order_blanket_order_carrier_auto_assign/) | 18.0.1.0.1 |  | Glue between sale_order_blanket_order and sale_order_carrier_auto_assign: keep auto-assigned carrier (delivery-fee) lines out of blanket-order call-off matching so they cannot consume blanket call-off capacity.
[sale_order_blanket_order_stock_prebook](sale_order_blanket_order_stock_prebook/) | 18.0.1.0.0 |  | Allow to prebook stock for blanket order
[sale_order_blanket_order_stock_prebook_release](sale_order_blanket_order_stock_prebook_release/) | 18.0.1.0.0 |  | Ensure that the date priotity when releasing qty is the start date of the blanker order

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
