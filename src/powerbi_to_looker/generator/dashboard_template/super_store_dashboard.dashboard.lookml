- dashboard: super_store_dashboard
  title: Super Store Dashboard
  preferred_viewer: dashboards-next
  description: ''
  preferred_slug: YNZuweXXmMibal4TnkrQPF
  theme_name: ''
  layout: newspaper
  tabs:
  - name: Summary
    label: Summary
  - name: Customer
    label: Customer
  - name: Sales
    label: Sales
  elements:
  - title: Summary
    name: Summary
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.total_sales]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: Net Revenue
    smart_single_value_size: false
    value_format: $#,##0,,"M"
    defaults_version: 1
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 2
    col: 0
    width: 6
    height: 3
    tab_name: Summary
  - title: Summary (Copy)
    name: Summary (Copy)
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.profit_sum]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: Net Profit
    smart_single_value_size: false
    value_format: ''
    defaults_version: 1
    hidden_pivots: {}
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 2
    col: 6
    width: 6
    height: 3
    tab_name: Summary
  - title: Revenue Trend Analysis
    name: Revenue Trend Analysis
    model: power_bi_looker
    explore: order_details
    type: looker_line
    fields: [order_details.profit_sum, order_details.total_sales, order_details.order_date_month_name]
    sorts: [order_details.order_date_month_name]
    limit: 500
    column_limit: 50
    dynamic_fields:
    - category: table_calculation
      expression: extract_months(${order_details.order_date_month})
      label: Month order
      value_format:
      value_format_name:
      _kind_hint: dimension
      table_calculation: month_order
      _type_hint: number
      is_disabled: true
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    y_axes: [{label: Total Sales and Total Profit, orientation: left, series: [{axisId: order_details.profit_sum,
            id: order_details.profit_sum, name: Profit}, {axisId: order_details.total_sales,
            id: order_details.total_sales, name: Sales}], showLabels: true, showValues: true,
        valueFormat: '$#,##0.00,,"M"', unpinAxis: false, tickDensity: custom, tickDensityCustom: 11,
        type: linear}]
    x_axis_label: Month
    x_axis_zoom: true
    y_axis_zoom: true
    hide_legend: true
    font_size: 9px
    label_value_format: $#,##0.00,,"M"
    series_colors:
      order_details.profit_sum: "#12239E"
      order_details.total_sales: "#118DFF"
    label_color: [grey]
    custom_color_enabled: true
    show_single_value_title: true
    single_value_title: Total Profit
    smart_single_value_size: false
    value_format: $#,##0,"K"
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    hidden_fields: []
    hidden_pivots: {}
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    table_theme: white
    header_text_alignment: left
    header_font_size: 12
    rows_font_size: 12
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 5
    col: 0
    width: 12
    height: 8
    tab_name: Summary
  - title: Summary (Copy 3)
    name: Summary (Copy 3)
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.total_orders]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: Total Transactions
    smart_single_value_size: false
    value_format: ''
    defaults_version: 1
    hidden_pivots: {}
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 2
    col: 18
    width: 6
    height: 3
    tab_name: Summary
  - title: Summary (Copy 2)
    name: Summary (Copy 2)
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.profit_margin__]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: Profit Margin
    smart_single_value_size: false
    value_format: ''
    defaults_version: 1
    hidden_pivots: {}
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 2
    col: 12
    width: 6
    height: 3
    tab_name: Summary
  - title: Revenue and Profit by Category
    name: Revenue and Profit by Category
    model: power_bi_looker
    explore: order_details
    type: looker_column
    fields: [order_details.total_sales, order_details.category, order_details.profit_sum]
    sorts: [order_details.total_sales desc 0]
    limit: 500
    column_limit: 50
    dynamic_fields:
    - category: table_calculation
      expression: extract_months(${order_details.order_date_month})
      label: Month order
      value_format:
      value_format_name:
      _kind_hint: dimension
      table_calculation: month_order
      _type_hint: number
      is_disabled: true
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    y_axes: [{label: Total Sales and Total Profit, orientation: left, series: [{axisId: order_details.profit_sum,
            id: order_details.profit_sum, name: Profit}, {axisId: order_details.total_sales,
            id: order_details.total_sales, name: Sales}], showLabels: true, showValues: true,
        valueFormat: '$#,##0.00,,"M"', unpinAxis: false, tickDensity: custom, tickDensityCustom: 11,
        type: linear}]
    x_axis_label: Category
    x_axis_zoom: true
    y_axis_zoom: true
    hide_legend: false
    font_size: 9px
    label_value_format: $#,##0.00,,"M"
    series_colors:
      order_details.total_sales: "#118DFF"
      order_details.profit_sum: "#12239E"
    label_color: [grey]
    show_null_points: true
    interpolation: linear
    custom_color_enabled: true
    show_single_value_title: true
    single_value_title: Total Profit
    smart_single_value_size: false
    value_format: $#,##0,"K"
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    hidden_fields: []
    hidden_pivots: {}
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    table_theme: white
    header_text_alignment: left
    header_font_size: 12
    rows_font_size: 12
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 5
    col: 12
    width: 12
    height: 8
    tab_name: Summary
  - name: ''
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: '[{"type":"h1","children":[{"text":"Executive Sales Performance Dashboard","bold":true,"color":"hsl(217,
      65%, 32%)"}],"align":"center"}]'
    rich_content_json: '{"format":"slate"}'
    row: 0
    col: 0
    width: 24
    height: 2
    tab_name: Summary
  - title: Total Orders
    name: Total Orders
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.total_orders]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    smart_single_value_size: false
    value_format: ''
    defaults_version: 1
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
    row: 5
    col: 0
    width: 4
    height: 3
    tab_name: Customer
  - title: Total Customers
    name: Total Customers
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.customer_count]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: ''
    smart_single_value_size: false
    defaults_version: 1
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
    row: 2
    col: 0
    width: 4
    height: 3
    tab_name: Customer
  - title: Revenue Distribution by Segment and Region
    name: Revenue Distribution by Segment and Region
    model: power_bi_looker
    explore: order_details
    type: looker_column
    fields: [order_details.region, order_details.segment, order_details.total_sales]
    pivots: [order_details.region]
    sorts: [order_details.region, order_details.total_sales desc 0]
    limit: 500
    column_limit: 50
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: left
    point_style: none
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    x_axis_zoom: true
    y_axis_zoom: true
    font_size: 10px
    label_value_format: $#,##0.00,,"M"
    series_colors:
      Central - order_details.total_sales: "#118DFF"
      East - order_details.total_sales: "#12239E"
      South - order_details.total_sales: "#E66C37"
      West - order_details.total_sales: "#6B007B"
    label_color: [grey]
    hidden_pivots: {}
    defaults_version: 1
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 8
    col: 0
    width: 24
    height: 6
    tab_name: Customer
  - title: Monthly Profit and Units Sold
    name: Monthly Profit and Units Sold
    model: power_bi_looker
    explore: order_details
    type: looker_line
    fields: [order_details.order_date_month_name, order_details.profit_sum, order_details.quantity]
    fill_fields: [order_details.order_date_month_name]
    sorts: [order_details.order_date_month_name]
    limit: 500
    column_limit: 50
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    y_axes: [{label: Total Profit and Total Quantity, orientation: left, series: [
          {axisId: order_details.profit_sum, id: order_details.profit_sum, name: Profit},
          {axisId: order_details.quantity, id: order_details.quantity, name: Quantity}],
        showLabels: true, showValues: true, unpinAxis: false, tickDensity: default,
        tickDensityCustom: 5, type: linear}]
    x_axis_zoom: true
    y_axis_zoom: true
    font_size: 9px
    label_value_format: '#,##0,"K"'
    series_colors:
      order_details.profit_sum: "#118DFF"
      order_details.quantity: "#12239E"
    label_color: [grey]
    defaults_version: 1
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 2
    col: 4
    width: 13
    height: 6
    tab_name: Customer
  - name: " (2)"
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: '[{"type":"h1","children":[{"text":"Customer Order Report","color":"hsl(217,
      65%, 32%)","bold":true}],"align":"center"}]'
    rich_content_json: '{"format":"slate"}'
    row: 0
    col: 0
    width: 24
    height: 2
    tab_name: Customer
  - title: Top Customers by Revenue
    name: Top Customers by Revenue
    model: power_bi_looker
    explore: total_orders_filtered
    type: looker_grid
    fields: [total_orders_filtered.customer_name, total_orders_filtered.total_orders,
      total_orders_filtered.sales]
    sorts: [total_orders_filtered.total_orders desc 0]
    limit: 500
    column_limit: 50
    total: true
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: false
    header_text_alignment: left
    header_font_size: '12'
    rows_font_size: '12'
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    show_sql_query_menu_options: false
    show_totals: true
    show_row_totals: true
    truncate_header: false
    minimum_column_width: 75
    series_cell_visualizations:
      total_orders_filtered.total_orders:
        is_active: false
    series_value_format:
      total_orders_filtered.sales:
        name: usd_0
        decimals: '0'
        format_string: "$#,##0"
        label: U.S. Dollars (0)
        label_prefix: U.S. Dollars
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    legend_position: center
    point_style: none
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    listen: {}
    row: 2
    col: 17
    width: 7
    height: 6
    tab_name: Customer
  - title: Revenue by Category
    name: Revenue by Category
    model: power_bi_looker
    explore: order_details
    type: looker_pie
    fields: [order_details.category, order_details.total_sales_in_K]
    sorts: [order_details.category]
    limit: 5000
    column_limit: 50
    value_labels: labels
    label_type: labPer
    start_angle: 150
    series_colors:
      Furniture: "#12239E"
      Office Supplies: "#E66C37"
      Technology: "#118DFF"
    show_value_labels: true
    font_size: 7
    hide_legend: false
    defaults_version: 1
    hidden_pivots: {}
    listen:
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 2
    col: 0
    width: 9
    height: 6
    tab_name: Sales
  - title: Regional Performance Comparison
    name: Regional Performance Comparison
    model: power_bi_looker
    explore: order_details
    type: looker_bar
    fields: [order_details.region, order_details.total_sales, order_details.profit_sum]
    sorts: [order_details.total_sales desc 0]
    limit: 5000
    column_limit: 50
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: none
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    x_axis_zoom: true
    y_axis_zoom: true
    font_size: 12px
    label_value_format: '#,##0.00,,"M"'
    series_colors:
      order_details.total_sales: "#118DFF"
      order_details.profit_sum: "#12239E"
    label_color: [grey]
    x_axis_datetime_label: ''
    defaults_version: 1
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 2
    col: 15
    width: 9
    height: 6
    tab_name: Sales
  - title: Summary (Copy 4)
    name: Summary (Copy 4)
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.total_sales]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: Net Revenue
    smart_single_value_size: false
    value_format: $#,##0,,"M"
    defaults_version: 1
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 2
    col: 9
    width: 6
    height: 3
    tab_name: Sales
  - title: Summary (Copy 5)
    name: Summary (Copy 5)
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.profit_sum]
    limit: 500
    column_limit: 50
    custom_color_enabled: true
    show_single_value_title: true
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    single_value_title: Net Profit
    smart_single_value_size: false
    value_format: ''
    defaults_version: 1
    hidden_pivots: {}
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 5
    col: 9
    width: 6
    height: 3
    tab_name: Sales
  - title: Monthly Revenue Trend
    name: Monthly Revenue Trend
    model: power_bi_looker
    explore: order_details
    type: looker_line
    fields: [order_details.total_sales, order_details.order_date_month_name]
    sorts: [order_details.order_date_month_name]
    limit: 500
    column_limit: 50
    dynamic_fields:
    - category: table_calculation
      expression: extract_months(${order_details.order_date_month})
      label: Month order
      value_format:
      value_format_name:
      _kind_hint: dimension
      table_calculation: month_order
      _type_hint: number
      is_disabled: true
    x_axis_gridlines: false
    y_axis_gridlines: true
    show_view_names: false
    show_y_axis_labels: true
    show_y_axis_ticks: true
    y_axis_tick_density: default
    y_axis_tick_density_custom: 5
    show_x_axis_label: true
    show_x_axis_ticks: true
    y_axis_scale_mode: linear
    x_axis_reversed: false
    y_axis_reversed: false
    plot_size_by_field: false
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    show_value_labels: true
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    interpolation: linear
    y_axes: [{label: Total Sales and Total Profit, orientation: left, series: [{axisId: order_details.profit_sum,
            id: order_details.profit_sum, name: Profit}, {axisId: order_details.total_sales,
            id: order_details.total_sales, name: Sales}], showLabels: true, showValues: true,
        valueFormat: '$#,##0.00,,"M"', unpinAxis: false, tickDensity: custom, tickDensityCustom: 11,
        type: linear}]
    x_axis_label: Month
    x_axis_zoom: true
    y_axis_zoom: true
    hide_legend: true
    font_size: 9px
    label_value_format: $#,##0.00,,"M"
    series_colors:
      order_details.total_sales: "#118DFF"
    label_color: [grey]
    custom_color_enabled: true
    show_single_value_title: true
    single_value_title: Total Profit
    smart_single_value_size: false
    value_format: $#,##0,"K"
    show_comparison: false
    comparison_type: value
    comparison_reverse_colors: false
    show_comparison_label: true
    enable_conditional_formatting: false
    conditional_formatting_include_totals: false
    conditional_formatting_include_nulls: false
    defaults_version: 1
    hidden_fields: []
    hidden_pivots: {}
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    table_theme: white
    header_text_alignment: left
    header_font_size: 12
    rows_font_size: 12
    listen:
      Segment: order_details.segment
      Category: order_details.category
      Region: order_details.region
      Date Range: order_details.order_date_date
    row: 8
    col: 0
    width: 24
    height: 6
    tab_name: Sales
  - name: " (3)"
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: '[{"type":"h1","children":[{"text":"Sales Performance Dashboard","bold":true,"color":"hsl(217,
      65%, 32%)"}],"align":"center"}]'
    rich_content_json: '{"format":"slate"}'
    row: 0
    col: 0
    width: 24
    height: 2
    tab_name: Sales
  filters:
  - name: Date Range
    title: Date Range
    type: field_filter
    default_value: 2014/03/01 to 2018/01/01
    allow_multiple_values: true
    required: false
    ui_config:
      type: day_range_picker
      display: inline
      options: []
    model: power_bi_looker
    explore: order_details
    listens_to_filters: []
    field: order_details.order_date_date
  - name: Segment
    title: Segment
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: checkboxes
      display: popover
    model: power_bi_looker
    explore: order_details
    listens_to_filters: []
    field: order_details.segment
  - name: Category
    title: Category
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: checkboxes
      display: popover
    model: power_bi_looker
    explore: order_details
    listens_to_filters: []
    field: order_details.category
  - name: Region
    title: Region
    type: field_filter
    default_value: ''
    allow_multiple_values: true
    required: false
    ui_config:
      type: checkboxes
      display: popover
    model: power_bi_looker
    explore: order_details
    listens_to_filters: []
    field: order_details.region
