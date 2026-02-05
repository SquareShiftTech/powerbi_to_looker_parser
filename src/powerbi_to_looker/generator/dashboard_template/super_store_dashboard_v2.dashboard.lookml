- dashboard: super_store_dashboard_v2
  title: Super Store Dashboard (v2)
  preferred_viewer: dashboards-next
  crossfilter_enabled: true
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
    width: 24
    height: 7
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
    row: 18
    col: 0
    width: 13
    height: 6
    tab_name: Summary
  - name: ''
    type: text
    title_text: ''
    subtitle_text: ''
    body_text: '[{"type":"h1","children":[{"text":"Super Store Dashboard (v2)","bold":true,"color":"hsl(217,
      65%, 32%)"}],"align":"center"}]'
    rich_content_json: '{"format":"slate"}'
    row: 0
    col: 0
    width: 24
    height: 2
    tab_name: Summary
  - title: Untitled
    name: Untitled
    model: power_bi_looker
    explore: order_details
    type: single_value
    fields: [order_details.quantity_sum]
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
    single_value_title: Total Quantity
    smart_single_value_size: false
    value_format: '#,##0,"K"'
    defaults_version: 1
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 2
    col: 18
    width: 6
    height: 3
    tab_name: Summary
  - title: Top 5 States by Revenue Performance
    name: Top 5 States by Revenue Performance
    model: power_bi_looker
    explore: order_details
    type: looker_funnel
    fields: [order_details.total_sales, order_details.state]
    filters:
      order_details.order_date_date: 2014/03/01 to 2018/01/01
      order_details.region: ''
      order_details.city: ''
      order_details.segment: ''
    sorts: [order_details.total_sales desc 0]
    limit: 5
    column_limit: 50
    leftAxisLabelVisible: false
    leftAxisLabel: ''
    rightAxisLabelVisible: false
    rightAxisLabel: ''
    smoothedBars: false
    orientation: automatic
    labelPosition: left
    percentType: total
    percentPosition: hidden
    valuePosition: right
    labelColorEnabled: false
    labelColor: "#FFF"
    color_application:
      collection_id: power-bi
      palette_id: power-bi-categorical-0
      options:
        steps: 5
        reverse: false
    isStepped: true
    labelScale: '0.9'
    labelOverlap: false
    defaults_version: 1
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 12
    col: 0
    width: 24
    height: 6
    tab_name: Summary
  - title: Regional Performance Breakdown
    name: Regional Performance Breakdown
    model: power_bi_looker
    explore: order_details
    type: looker_grid
    fields: [order_details.region, order_details.total_sales, order_details.profit_sum,
      order_details.profit_sum_margin__]
    filters:
      order_details.region: ''
      order_details.city: ''
      order_details.segment: ''
    sorts: [order_details.profit_sum desc]
    limit: 500
    column_limit: 50
    show_view_names: false
    show_row_numbers: true
    transpose: false
    truncate_text: true
    hide_totals: false
    hide_row_totals: false
    size_to_fit: true
    table_theme: white
    limit_displayed_rows: false
    enable_conditional_formatting: true
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
    series_labels:
      order_details.total_sales: Total Sales
    series_cell_visualizations:
      order_details.profit_sum:
        is_active: false
    conditional_formatting: [{type: along a scale..., value: !!null '', fields: [
          order_details.profit_sum_margin__], apply_formatting_to_row: false, cell_format: {
          background_color: "#4E79A7", font_color: !!null '', color_application: {
            collection_id: verizon, custom: {id: 933d19eb-1134-dd34-f951-3f099f7d346a,
              label: Custom, type: continuous, stops: [{color: "#D26565", offset: 0},
                {color: "#48BC66", offset: 100}]}, options: {steps: 5, mirror: false,
              reverse: false, stepped: false}}, font_style: {bold: false, italic: false,
            strikethrough: false}}, row_format: {background_color: "#F3F367", font_color: !!null '',
          color_application: {collection_id: verizon, options: {mirror: false, reverse: false,
              stepped: false}}, font_style: {bold: false, italic: false, strikethrough: false}},
        apply_to: selectFields}, {type: along a scale..., value: !!null '', fields: [
          order_details.profit_sum], apply_formatting_to_row: false, cell_format: {background_color: "#4E79A7",
          font_color: !!null '', color_application: {collection_id: verizon, custom: {
              id: 64bcd8d7-6417-b3b7-abd9-6f573c5d4de2, label: Custom, type: continuous,
              stops: [{color: "#D26565", offset: 0}, {color: "#48BC66", offset: 100}]},
            options: {steps: 5, mirror: false, reverse: false, stepped: false}}, font_style: {
            bold: false, italic: false, strikethrough: false}}, row_format: {background_color: "#F3F367",
          font_color: !!null '', color_application: {collection_id: verizon, options: {
              mirror: false, reverse: false, stepped: false}}, font_style: {bold: false,
            italic: false, strikethrough: false}}, apply_to: selectFields}, {type: along
          a scale..., value: !!null '', fields: [order_details.total_sales], apply_formatting_to_row: false,
        cell_format: {background_color: "#4E79A7", font_color: !!null '', color_application: {
            collection_id: verizon, custom: {id: fb521787-6c6e-e031-7dca-d21897f598cd,
              label: Custom, type: continuous, stops: [{color: "#D26565", offset: 0},
                {color: "#48BC66", offset: 100}]}, options: {steps: 5, mirror: false,
              reverse: false, stepped: false}}, font_style: {bold: false, italic: false,
            strikethrough: false}}, row_format: {background_color: "#F3F367", font_color: !!null '',
          color_application: {collection_id: verizon, options: {mirror: false, reverse: false,
              stepped: false}}, font_style: {bold: false, italic: false, strikethrough: false}},
        apply_to: selectFields}]
    series_value_format:
      order_details.total_sales:
        name: usd_0
        decimals: '0'
        format_string: "$#,##0"
        label: U.S. Dollars (0)
        label_prefix: U.S. Dollars
      order_details.profit_sum:
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
    hidden_pivots: {}
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 18
    col: 13
    width: 11
    height: 6
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
    fields: [order_details.order_date_month_name, order_details.profit_sum, order_details.quantity_sum]
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
          {axisId: order_details.quantity_sum, id: order_details.quantity_sum, name: Quantity}],
        showLabels: true, showValues: true, unpinAxis: false, tickDensity: default,
        tickDensityCustom: 5, type: linear}]
    x_axis_zoom: true
    y_axis_zoom: true
    font_size: 9px
    label_value_format: '#,##0,"K"'
    series_colors:
      order_details.profit_sum: "#118DFF"
      order_details.quantity_sum: "#12239E"
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
    explore: order_details
    type: looker_grid
    fields: [order_details.customer_name, order_details.total_orders,
      order_details.total_sales]
    sorts: [order_details.total_orders desc 0]
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
      order_details.total_orders:
        is_active: false
    defaults_version: 1
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 2
    col: 17
    width: 7
    height: 6
    tab_name: Customer
  - title: Customer Segment Profitability
    name: Customer Segment Profitability
    model: power_bi_looker
    explore: order_details
    type: looker_pie
    fields: [order_details.segment, order_details.profit_sum]
    filters:
      order_details.region: ''
      order_details.city: ''
      order_details.segment: ''
    sorts: [order_details.profit_sum desc 0]
    limit: 500
    column_limit: 50
    value_labels: legend
    label_type: labVal
    series_colors:
      Consumer: "#118DFF"
      Corporate: "#12239E"
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
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 14
    col: 0
    width: 8
    height: 6
    tab_name: Customer
  - title: Discount Impact Analysis
    name: Discount Impact Analysis
    model: power_bi_looker
    explore: order_details
    type: looker_scatter
    fields: [order_details.total_sales, order_details.sub_category, order_details.profit_sum_margin__,
      order_details.avg_discount]
    filters:
      order_details.region: ''
      order_details.city: ''
      order_details.segment: ''
    sorts: [order_details.total_sales desc]
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
    plot_size_by_field: true
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    show_value_labels: false
    label_density: 25
    x_axis_scale: auto
    y_axis_combined: true
    show_null_points: true
    color_application:
      collection_id: verizon
      custom:
        id: 86d56658-273b-5267-bbb8-beca69bffc64
        label: Custom
        type: discrete
        colors:
        - "#3ca68a"
        - "#F28E2B"
        - "#E15759"
        - "#76B7B2"
        - "#59A14F"
        - "#EDC948"
        - "#B07AA1"
        - "#FF9DA7"
        - "#BAB0AC"
      options:
        steps: 5
    size_by_field: order_details.avg_discount
    x_axis_zoom: true
    y_axis_zoom: true
    series_colors: {}
    label_color: [grey]
    swap_axes: true
    cluster_points: false
    quadrants_enabled: false
    quadrant_properties:
      '0':
        color: ''
        label: Quadrant 1
      '1':
        color: ''
        label: Quadrant 2
      '2':
        color: ''
        label: Quadrant 3
      '3':
        color: ''
        label: Quadrant 4
    custom_quadrant_point_x: 5
    custom_quadrant_point_y: 5
    custom_x_column: order_details.total_sales
    custom_y_column: order_details.avg_discount
    custom_value_label_column: ''
    series_tooltip_options:
      order_details.avg_discount:
        custom_tooltips_enabled: true
        style:
          border_radius: 4
        template: |2-

                      <div class="section">
                        <div>Sub Category</div>
                        <div class="value">{{ order_details.sub_category }}</div>
                      </div>
                      <div class="section">
                        <div>Category</div>
                        <div class="value">{{ order_details.category }}</div>
                      </div><div class="section">
                <div>Avg Discount</div>
                <div class="value">{{ order_details.avg_discount }}</div>
              </div>
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 1
    hidden_pivots: {}
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 14
    col: 8
    width: 16
    height: 6
    tab_name: Customer
  - title: Revenue by Category
    name: Revenue by Category
    model: power_bi_looker
    explore: order_details
    type: looker_pie
    fields: [order_details.category, order_details.total_sales]
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
  - title: Geographic Sales Performance
    name: Geographic Sales Performance
    model: power_bi_looker
    explore: order_details
    type: looker_google_map
    fields: [order_details.state, order_details.total_sales]
    filters:
      order_details.region: ''
      order_details.city: ''
      order_details.segment: ''
    sorts: [order_details.total_sales desc 0]
    limit: 500
    column_limit: 50
    hidden_fields: []
    hidden_points_if_no: []
    series_labels: {}
    show_view_names: false
    map_plot_mode: points
    heatmap_gridlines: false
    heatmap_gridlines_empty: false
    heatmap_opacity: 0.5
    show_region_field: true
    draw_map_labels_above_data: true
    map_tile_provider: light
    map_position: fit_data
    map_pannable: true
    map_zoomable: true
    map_marker_type: circle
    map_marker_icon_name: default
    map_marker_radius_mode: proportional_value
    map_marker_units: meters
    map_marker_proportional_scale_type: linear
    map_marker_color_mode: fixed
    show_legend: true
    quantize_map_value_colors: false
    reverse_map_value_colors: true
    map: usa
    map_projection: ''
    color_application:
      collection_id: verizon
      custom:
        id: 86d56658-273b-5267-bbb8-beca69bffc64
        label: Custom
        type: discrete
        colors:
        - "#3ca68a"
        - "#F28E2B"
        - "#E15759"
        - "#76B7B2"
        - "#59A14F"
        - "#EDC948"
        - "#B07AA1"
        - "#FF9DA7"
        - "#BAB0AC"
      options:
        steps: 5
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
    size_by_field: order_details.total_sales
    plot_size_by_field: true
    x_axis_zoom: true
    y_axis_zoom: true
    trellis: ''
    stacking: ''
    limit_displayed_rows: false
    legend_position: center
    point_style: circle
    series_colors: {}
    show_value_labels: false
    label_density: 25
    label_color: [grey]
    x_axis_scale: auto
    y_axis_combined: true
    swap_axes: true
    show_null_points: true
    cluster_points: false
    quadrants_enabled: false
    quadrant_properties:
      '0':
        color: ''
        label: Quadrant 1
      '1':
        color: ''
        label: Quadrant 2
      '2':
        color: ''
        label: Quadrant 3
      '3':
        color: ''
        label: Quadrant 4
    custom_quadrant_point_x: 5
    custom_quadrant_point_y: 5
    custom_x_column: order_details.total_sales
    custom_y_column: order_details.avg_discount
    custom_value_label_column: ''
    ordering: none
    show_null_labels: false
    show_totals_labels: false
    show_silhouette: false
    totals_color: "#808080"
    defaults_version: 0
    hidden_pivots: {}
    listen:
      Date Range: order_details.order_date_date
      Region: order_details.region
      Segment: order_details.segment
      Category: order_details.category
    row: 14
    col: 0
    width: 24
    height: 7
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
