# Dashboard template update plan

## Goal

Provide a dashboard template that matches the **latest manual dashboard** (`lookml_output/manual.dashboard.dashboard.lookml`) in layout and structure, while using our **generated semantic** (model name, explore, and field names from generated LookML).

**Decision:** Create a **v2 template** (`super_store_dashboard_v2.dashboard.lookml`) and leave the existing `super_store_dashboard.dashboard.lookml` unchanged. The generator emits both templates when present.

## Source vs target

| Item | Manual (source) | Our semantic (target) |
|------|-----------------|------------------------|
| File | `lookml_output/manual.dashboard.dashboard.lookml` | `src/powerbi_to_looker/generator/dashboard_template/super_store_dashboard.dashboard.lookml` |
| Dashboard id | `executive_sales_performance_dashboard` | `super_store_dashboard` |
| Title | Executive Sales Performance Dashboard | Super Store Dashboard |
| Model | `powerbi_to_looker` | `power_bi_looker` |
| Explore | `order_details` (and `total_orders_filtered`) | `order_details` only |

## Field mappings (manual → our view)

From generated `order_details.view.lkml`:

| Manual field | Our field | Notes |
|--------------|-----------|--------|
| `order_details.sales` | `order_details.total_sales` | We use measure for tiles/charts; we have dimension `sales` and measures `sales_sum` / `total_sales` |
| `order_details.profit` | `order_details.profit_sum` | Measure for aggregation |
| `order_details.order_month_name` | `order_details.order_date_month_name` | From dimension_group `order_date` |
| `order_details.order_month` | `order_details.order_date_month` | Same |
| `order_details.order_date` (filter/listen) | `order_details.order_date_date` | Date filter uses date timeframe |
| `order_details.profit_margin_pct` | `order_details.profit_margin__` | Generated measure name |
| `order_details.sales_in_K` | `order_details.total_sales` | No `sales_in_K` in view |
| `order_details.quantity` (in tiles/charts) | `order_details.quantity_sum` | Measure for aggregation |
| `total_orders_filtered.customer_name` | `order_details.customer_name` | Use order_details explore |
| `total_orders_filtered.total_orders` | `order_details.total_orders` | Same measure name |
| `total_orders_filtered.sales` | `order_details.total_sales` | Same as above |

## Implementation steps

1. **Replace template content**  
   Copy the full content of `manual.dashboard.dashboard.lookml` into `super_store_dashboard.dashboard.lookml` (template path). This brings all new manual layout, tabs, elements, and filters.

2. **Apply string replacements in order** (most specific first to avoid double-replace):
   - `total_orders_filtered.customer_name` → `order_details.customer_name`
   - `total_orders_filtered.total_orders` → `order_details.total_orders`
   - `total_orders_filtered.sales` → `order_details.total_sales`
   - `powerbi_to_looker` → `power_bi_looker`
   - `executive_sales_performance_dashboard` → `super_store_dashboard`
   - `Executive Sales Performance Dashboard` → `Super Store Dashboard`
   - `order_details.order_month_name` → `order_details.order_date_month_name`
   - `order_details.order_month` → `order_details.order_date_month`
   - `order_details.profit_margin_pct` → `order_details.profit_margin__`
   - `order_details.sales_in_K` → `order_details.total_sales`
   - `order_details.sales` → `order_details.total_sales`
   - `order_details.profit` → `order_details.profit_sum`
   - `Date Range: order_details.order_date` → `Date Range: order_details.order_date_date`
   - `field: order_details.order_date` → `field: order_details.order_date_date`
   - `order_details.order_date: ` → `order_details.order_date_date: ` (filter key in element filters)
   - `order_details.quantity` → `order_details.quantity_sum`

3. **Verify**  
   Grep the template for any leftover: `powerbi_to_looker`, `order_month` (without `order_date_`), `total_orders_filtered`, `sales_in_K`, `profit_margin_pct`, or bare `order_details.order_date` (ensure only `order_date_date` / `order_date_month` etc. remain).

## Result

- Template will have the same layout and tiles as the manual dashboard (Summary / Customer / Sales tabs, all tiles, filters).
- All references will use `power_bi_looker` and `order_details` with our generated field names, so the dashboard works with the output of the migration pipeline.
