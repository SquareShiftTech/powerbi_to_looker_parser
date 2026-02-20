
view: dim_date {

  
  sql_table_name: `tableau-to-looker-migration.education.dim_date` ;;
  

  
  
  
  dimension: academic_year {
    type: string
    sql: ${TABLE}.academic_year ;;
    
    label: "academic_year"
    
  }
  
  
  
  
  dimension: day_name {
    type: string
    sql: ${TABLE}.day_name ;;
    
    label: "day_name"
    
  }
  
  
  
  
  dimension: is_holiday {
    type: yesno
    sql: ${TABLE}.is_holiday ;;
    
    label: "is_holiday"
    
  }
  
  
  
  
  dimension: is_weekend {
    type: yesno
    sql: ${TABLE}.is_weekend ;;
    
    label: "is_weekend"
    
  }
  
  
  
  
  dimension: month_name {
    type: string
    sql: ${TABLE}.month_name ;;
    
    label: "month_name"
    
  }
  
  
  
  
  dimension: quarter {
    type: string
    sql: ${TABLE}.quarter ;;
    
    label: "quarter"
    
  }
  
  
  
  
  dimension: semester {
    type: string
    sql: ${TABLE}.semester ;;
    
    label: "semester"
    
  }
  
  
  
  dimension_group: full_date {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.full_date ;;
    
    label: "full_date"
    
  }
  
  
  
  
  
  dimension: date_key_measure {
    type: sum
    sql: ${TABLE}.date_key ;;
    
  }

  measure: date_key {
    type: sum
    sql: ${ date_key_measure } ;;
    
    
    label: "date_key"
    
  }
  
  
  
  
  
  dimension: day_measure {
    type: sum
    sql: ${TABLE}.day ;;
    
  }

  measure: day {
    type: sum
    sql: ${ day_measure } ;;
    
    
    label: "day"
    
  }
  
  
  
  
  
  dimension: day_of_week_measure {
    type: sum
    sql: ${TABLE}.day_of_week ;;
    
  }

  measure: day_of_week {
    type: sum
    sql: ${ day_of_week_measure } ;;
    
    
    label: "day_of_week"
    
  }
  
  
  
  
  
  dimension: month_measure {
    type: sum
    sql: ${TABLE}.month ;;
    
  }

  measure: month {
    type: sum
    sql: ${ month_measure } ;;
    
    
    label: "month"
    
  }
  
  
  
  
  
  dimension: year_measure {
    type: sum
    sql: ${TABLE}.year ;;
    
  }

  measure: year {
    type: sum
    sql: ${ year_measure } ;;
    
    
    label: "year"
    
  }
  
  
}