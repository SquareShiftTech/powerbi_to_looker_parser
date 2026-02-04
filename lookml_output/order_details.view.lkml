view: order_details {

  sql_table_name: dbo.Order_Details ;;
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
  measure: region_id {
    type: sum
    sql: ${region_id} ;;
    label: "Region_ID"
    value_format: "#,##0.00"
    format: "decimal_2"
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
  measure: total_sales {
    type: sum
    sql: ${sales} ;;
    label: "Total Sales"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: total_profit {
    type: sum
    sql: ${profit} ;;
    label: "Total Profit"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: total_quantity {
    type: sum
    sql: ${quantity} ;;
    label: "Total Quantity"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: profit_margin__ {
    type: number
    sql: IFNULL(SAFE_DIVIDE(${total_profit}, ${total_sales}), 0) ;;
    label: "Profit Margin %"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: product_rank {
    type: sum
    sql: NULL ;;
    label: "Product Rank"
    value_format: "#,##0.00"
    format: "decimal_2"
    description: "DAX: RANKX (
    ALL ( Order_Details[Product_Name] ),
    [Total Sales],
    ,
    DESC
)"
  }
  measure: customer_count {
    type: count
    sql: ${customer_id} ;;
    label: "Customer Count"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
}