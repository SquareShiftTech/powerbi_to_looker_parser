view: order_details {
  sql_table_name: `tableau-to-looker-migration.Super_Store_Sales.Order_Details` ;;

  dimension: category {
    type: string
    sql: ${TABLE}.Category ;;
  }
  dimension: city {
    type: string
    sql: ${TABLE}.City ;;
  }
  dimension: country {
    type: string
    map_layer_name: countries
    sql: ${TABLE}.Country ;;
  }
  dimension: customer_id {
    type: string
    sql: ${TABLE}.Customer_ID ;;
  }
  dimension: customer_name {
    type: string
    sql: ${TABLE}.Customer_Name ;;
  }
  dimension_group: order {
    type: time
    timeframes: [raw, date, week, month, quarter, year,month_name,month_num]
    convert_tz: no
    datatype: date
    sql: ${TABLE}.Order_Date ;;
  }
  dimension: order_id {
    type: string
    # hidden: yes
    sql: ${TABLE}.Order_ID ;;
  }
  dimension: postal_code {
    type: zipcode
    sql: ${TABLE}.Postal_Code ;;
  }
  dimension: product_id {
    type: string
    sql: ${TABLE}.Product_ID ;;
  }
  dimension: product_name {
    type: string
    sql: ${TABLE}.Product_Name ;;
  }
  dimension: region {
    type: string
    sql: ${TABLE}.Region ;;
  }
  dimension: region_id {
    type: number
    # hidden: yes
    sql: ${TABLE}.Region_ID ;;
  }
  dimension: segment {
    type: string
    sql: ${TABLE}.Segment ;;
  }
  dimension_group: ship {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    convert_tz: no
    datatype: date
    sql: ${TABLE}.Ship_Date ;;
  }
  dimension: ship_mode {
    type: string
    sql: ${TABLE}.Ship_Mode ;;
  }
  dimension: state {
    type: string
    map_layer_name: us_states
    sql: ${TABLE}.State ;;
  }
  dimension: sub_category {
    type: string
    sql: ${TABLE}.Sub_Category ;;
  }
  measure: count {
    type: count
    drill_fields: [detail*]
  }

  measure: sales {
    type: sum
    label: "Total Sales"
    sql: ${TABLE}.Sales ;;
    value_format: "$#,##0.00,,\"M\""
  }

  measure: sales_in_K{
    type: sum
    label: "Total Sales in K"
    sql: ${TABLE}.Sales ;;
    value_format: "$#,##0,\"K\""
  }

  measure: discount {
    type: sum
    value_format_name: usd
    sql: ${TABLE}.Discount ;;
  }

  measure: profit {
    type: sum
    sql: ${TABLE}.Profit ;;
    value_format: "$#,##0,\"K\""
  }
  measure: quantity {
    type: sum
    sql: ${TABLE}.Quantity ;;
  }

  measure: profit_margin_pct {
    type: number
    label: "Profit Margin %"
    sql: SAFE_DIVIDE(${profit}, ${sales}) ;;
    value_format_name: percent_2
  }

  measure: product_rank {
    type: number
    label: "Product Rank"
    sql: RANK() OVER (ORDER BY ${sales} DESC) ;;
  }

  measure: customer_count {
    type: count_distinct
    label: "Customer Count"
    sql: ${customer_id} ;;
    value_format: "#,##0,\"K\""
  }

  measure: total_orders {
    type: count_distinct
    label: "Total Orders"
    sql: ${order_id} ;;
    value_format: "#,##0,\"K\""
  }


  measure: sales_py {
    type: sum
    label: "Sales PY"
    sql: ${TABLE}.Sales ;;
    filters: [order_date: "1 year ago for 1 year"]
    description: "Sales for same period last year"
  }

  # measure: sales_py {
  #   type: sum
  #   label: "Sales Prior Year"
  #   sql: ${TABLE}.Sales ;;
  #   filters: [order_raw: "1 year"]
  #   description: "Sales for prior year period"
  # }

  measure: yoy_growth_pct {
    type: number
    label: "YoY Growth %"
    sql: COALESCE(SAFE_DIVIDE(${sales} - ${sales_py}, ${sales_py}), 0) ;;
    value_format_name: percent_2
    description: "Year-over-year sales growth percentage"
  }

  measure: sales_ytd {
    type: sum
    label: "Sales YTD"
    sql: ${TABLE}.Sales ;;
    filters: [order_date: "this year"]
    description: "Year-to-date sales"
  }

  measure: avg_discount {
    type: average
    sql: ${TABLE}.Discount ;;
  }

  # ----- Sets of fields for drilling ------
  set: detail {
    fields: [
  customer_name,
  product_name,
  orders.order_id,
  orders.customer_name,
  orders.product_name,
  region.id
  ]
  }

}
