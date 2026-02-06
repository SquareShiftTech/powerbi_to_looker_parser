view: order_details {

  sql_table_name: `tableau-to-looker-migration.Super_Store_Sales.Order_Details` ;;
  dimension: order_id {
    type: string
    sql: ${TABLE}.Order_ID ;;
    label: "Order_ID"
  }
  dimension_group: order_date {
    type: time
    timeframes: [raw, date, week, month, quarter, year, month_name, month_num]
    sql: TIMESTAMP(DATE(${TABLE}.Order_Date)) ;;
    label: "Order_Date"
  }
  dimension_group: ship_date {
    type: time
    timeframes: [raw, date, week, month, quarter, year, month_name, month_num]
    sql: TIMESTAMP(DATE(${TABLE}.Ship_Date)) ;;
    label: "Ship_Date"
  }
  dimension: ship_mode {
    type: string
    sql: ${TABLE}.Ship_Mode ;;
    label: "Ship_Mode"
  }
  dimension: customer_id {
    type: string
    sql: ${TABLE}.Customer_ID ;;
    label: "Customer_ID"
  }
  dimension: customer_name {
    type: string
    sql: ${TABLE}.Customer_Name ;;
    label: "Customer_Name"
  }
  dimension: segment {
    type: string
    sql: ${TABLE}.Segment ;;
    label: "Segment"
  }
  dimension: country {
    type: string
    sql: ${TABLE}.Country ;;
    label: "Country"
  }
  dimension: city {
    type: string
    sql: ${TABLE}.City ;;
    label: "City"
  }
  dimension: state {
    type: string
    sql: ${TABLE}.State ;;
    label: "State"
    map_layer_name: us_states
  }
  dimension: postal_code {
    type: string
    sql: ${TABLE}.Postal_Code ;;
    label: "Postal_Code"
  }
  dimension: region {
    type: string
    sql: ${TABLE}.Region ;;
    label: "Region"
  }
  dimension: product_id {
    type: string
    sql: ${TABLE}.Product_ID ;;
    label: "Product_ID"
  }
  dimension: category {
    type: string
    sql: ${TABLE}.Category ;;
    label: "Category"
  }
  dimension: sub_category {
    type: string
    sql: ${TABLE}.Sub_Category ;;
    label: "Sub_Category"
  }
  dimension: product_name {
    type: string
    sql: ${TABLE}.Product_Name ;;
    label: "Product_Name"
  }
  dimension: region_id {
    type: number
    sql: ${TABLE}.Region_ID ;;
    label: "Region_ID"
  }
  dimension: sales {
    type: number
    sql: ${TABLE}.Sales ;;
    label: "Sales"
  }
  dimension: quantity {
    type: number
    sql: ${TABLE}.Quantity ;;
    label: "Quantity"
  }
  dimension: discount {
    type: number
    sql: ${TABLE}.Discount ;;
    label: "Discount"
  }
  dimension: profit {
    type: number
    sql: ${TABLE}.Profit ;;
    label: "Profit"
  }
  measure: region_id_sum {
    type: sum
    sql: ${region_id} ;;
    label: "Region_ID"
    value_format: "#,##0.00"
  }
  measure: sales_sum {
    type: sum
    sql: ${sales} ;;
    label: "Sales"
    value_format: "#,##0.00"
  }
  measure: quantity_sum {
    type: sum
    sql: ${quantity} ;;
    label: "Quantity"
    value_format: "#,##0.00"
  }
  measure: discount_sum {
    type: sum
    sql: ${discount} ;;
    label: "Discount"
    value_format: "#,##0.00"
  }
  measure: profit_sum {
    type: sum
    sql: ${profit} ;;
    label: "Profit"
    value_format: "#,##0.00"
  }
  measure: total_sales {
    type: sum
    sql: ${sales} ;;
    label: "Total Sales"
    value_format: "#,##0.00"
  }
  measure: total_profit {
    type: sum
    sql: ${profit} ;;
    label: "Total Profit"
    value_format: "#,##0.00"
  }
  measure: total_quantity {
    type: sum
    sql: ${quantity} ;;
    label: "Total Quantity"
    value_format: "#,##0.00"
  }
  measure: profit_margin__ {
    type: number
    sql: IFNULL(SAFE_DIVIDE(${total_profit}, ${total_sales}), 0) ;;
    label: "Profit Margin %"
    value_format: "#,##0.00"
  }
  measure: product_rank {
    type: number
    sql: RANK() OVER (ORDER BY ${total_sales} DESC) ;;
    label: "Product Rank"
    value_format: "#,##0.00"
  }
  measure: customer_count {
    type: count_distinct
    sql: ${customer_id} ;;
    label: "Customer Count"
    value_format: "#,##0.00"
  }
  measure: total_orders {
    type: count_distinct
    sql: ${order_id} ;;
    label: "Total_Orders"
    value_format: "#,##0.00"
  }
  measure: high_discount_flag {
    type: average
    sql: ${discount} ;;
    label: "High Discount Flag"
    value_format: "#,##0.00"
  }
  measure: total_returns {
    type: count
    sql: ${order_id} ;;
    label: "Total returns"
    value_format: "#,##0.00"
  }
  measure: avg_discount {
    type: average
    sql: ${discount} ;;
    label: "Avg Discount"
    value_format: "#,##0.00"
  }
}