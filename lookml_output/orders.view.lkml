view: orders {

  sql_table_name: dbo.Orders ;;
  dimension: order_id {
    type: string
    sql: ${TABLE}.Order_ID ;;
    label: "Order_ID"
  }
  dimension: order_date {
    type: time
    sql: DATE(${TABLE}.Order_Date) ;;
    label: "Order_Date"
    datetype: date
    timeframes: [day, week, month, quarter, year]
  }
  dimension: ship_date {
    type: time
    sql: DATE(${TABLE}.Ship_Date) ;;
    label: "Ship_Date"
    datetype: date
    timeframes: [day, week, month, quarter, year]
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
  measure: sales {
    type: sum
    sql: ${sales} ;;
    label: "Sales"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: quantity {
    type: sum
    sql: ${quantity} ;;
    label: "Quantity"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: discount {
    type: sum
    sql: ${discount} ;;
    label: "Discount"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: profit {
    type: sum
    sql: ${profit} ;;
    label: "Profit"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: total_orders {
    type: count_distinct
    sql: ${order_id} ;;
    label: "Total Orders"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: sales_by_year {
    type: sum
    sql: NULL ;;
    label: "Sales by Year"
    value_format: "#,##0.00"
    format: "decimal_2"
    description: "DAX: CALCULATE (
    [Total Sales],
    YEAR ( Orders[Order_Date] )
)"
  }
  measure: sales_ytd {
    type: sum
    sql: NULL ;;
    label: "Sales YTD"
    value_format: "#,##0.00"
    format: "decimal_2"
    description: "DAX: TOTALYTD (
    [Total Sales],
    Orders[Order_Date]
)"
  }
  measure: sales_py {
    type: sum
    sql: NULL ;;
    label: "Sales PY"
    value_format: "#,##0.00"
    format: "decimal_2"
    description: "DAX: CALCULATE (
    [Total Sales],
    SAMEPERIODLASTYEAR ( Orders[Order_Date] )
)"
  }
  measure: yoy_growth__ {
    type: sum
    sql: NULL ;;
    label: "YoY Growth %"
    value_format: "#,##0.00"
    format: "decimal_2"
    description: "DAX: DIVIDE ( [Total Sales] - [Sales PY], [Sales PY], 0 )"
  }
}