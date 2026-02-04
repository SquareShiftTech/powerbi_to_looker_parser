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
}
explore: region {
  label: "Region"
}
