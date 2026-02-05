view: returns {

  sql_table_name: `tableau-to-looker-migration.Super_Store_Sales.Returns` ;;
  dimension: returned {
    type: string
    sql: ${TABLE}.Returned ;;
    label: "Returned"
  }
  dimension: order_id {
    type: string
    sql: ${TABLE}.Order_ID ;;
    label: "Order_ID"
  }
  measure: count {
    type: count
    sql: * ;;
    label: "Count"
    value_format: "#,##0"
    format: "decimal_2"
  }
}