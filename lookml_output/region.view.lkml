view: region {

  sql_table_name: dbo.Region ;;
  dimension: region {
    type: string
    sql: ${TABLE}.Region ;;
    label: "Region"
  }
  dimension: id {
    type: number
    sql: ${TABLE}.ID ;;
    label: "ID"
  }
  measure: id {
    type: sum
    sql: ${id} ;;
    label: "ID"
    value_format: "#,##0.00"
    format: "decimal_2"
  }
}