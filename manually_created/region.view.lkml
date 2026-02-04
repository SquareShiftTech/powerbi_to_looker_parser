view: region {
  sql_table_name: `tableau-to-looker-migration.Super_Store_Sales.Region` ;;
  drill_fields: [id]

  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.ID ;;
  }
  dimension: region {
    type: string
    sql: ${TABLE}.Region ;;
  }
  measure: count {
    type: count
    drill_fields: [id, order_details.count]
  }
}
