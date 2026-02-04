view: returns {
  sql_table_name: `tableau-to-looker-migration.Super_Store_Sales.Returns` ;;

  dimension: order_id {
    type: string
    # hidden: yes
    sql: ${TABLE}.Order_ID ;;
  }
  dimension: returned {
    type: yesno
    sql: ${TABLE}.Returned ;;
  }
  measure: count {
    type: count
    drill_fields: [orders.order_id, orders.customer_name, orders.product_name]
  }

  measure: total_orders {
    type: count_distinct
    label: "Total Orders"
    sql: ${order_id} ;;
  }

  measure: returned_orders {
    type: count_distinct
    label: "Returned Orders"
    sql: ${returns.order_id} ;;
    filters: [returns.returned: "Yes"]
  }

  measure: return_rate_pct {
    type: number
    label: "Return Rate %"
    sql: COALESCE(SAFE_DIVIDE(${returned_orders}, ${total_orders}), 0) ;;
    value_format_name: percent_2
  }
}
