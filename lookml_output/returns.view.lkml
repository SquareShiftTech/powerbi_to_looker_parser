view: returns {

  sql_table_name: dbo.Returns ;;
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
  measure: returned_orders {
    type: count_distinct
    sql: ${order_id} ;;
    label: "Returned Orders"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
  measure: return_rate__ {
    type: number
    sql: IFNULL(SAFE_DIVIDE(${returned_orders}, ${total_orders}), 0) ;;
    label: "Return Rate %"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
}