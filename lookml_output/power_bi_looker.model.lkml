include: "*.view.lkml"
include: "*.dashboard.lookml"

connection: "t2l"

explore: order_details {
  label: "Order_Details"
  join: region {
    type: left_outer
    sql_on: ${order_details.region} = ${region.region} ;;
    relationship: many_to_one
  }
  join: returns {
    type: left_outer
    sql_on: ${order_details.order_id} = ${returns.order_id} ;;
    relationship: many_to_one
  }
}
explore: region {
  label: "Region"
}
explore: returns {
  label: "Returns"
}
