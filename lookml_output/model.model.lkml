connection: "powerbi_connection"

explore: order_details {
  view: order_details
  label: "Order_Details"
}
explore: orders {
  view: orders
  label: "Orders"
  join: region {
    view: region
    type: left_outer
    sql_on: ${orders.order_id} = ${region.id} ;;
    relationship: many_to_one
  }
  join: returns {
    view: returns
    type: left_outer
    sql_on: ${orders.order_id} = ${returns.order_id} ;;
    relationship: many_to_one
  }
  join: order_details {
    view: order_details
    type: left_outer
    sql_on: ${orders.order_id} = ${order_details.order_id} ;;
    relationship: many_to_one
  }
}
explore: region {
  view: region
  label: "Region"
}
explore: returns {
  view: returns
  label: "Returns"
}
