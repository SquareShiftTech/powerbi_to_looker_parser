
view: localdatetable_a5fd9646_2978_429d_bb4f_ce757eecfbb5 {

  

  
  
  
  # Original DAX: DAY([Date])
  
  # Converted: auto
  
  
  dimension: day {
    type: number
    sql: NULL ;;
    
    label: "Day"
    
  }
  
  
  
  
  # Original DAX: FORMAT([Date], "MMMM")
  
  # Converted: auto
  
  
  dimension: month {
    type: string
    sql: NULL ;;
    
    label: "Month"
    
  }
  
  
  
  
  # Original DAX: MONTH([Date])
  
  # Converted: auto
  
  
  dimension: monthno {
    type: number
    sql: NULL ;;
    
    label: "MonthNo"
    
  }
  
  
  
  
  # Original DAX: "Qtr " & [QuarterNo]
  
  # Converted: auto
  
  
  dimension: quarter {
    type: string
    sql: NULL ;;
    
    label: "Quarter"
    
  }
  
  
  
  
  # Original DAX: INT(([MonthNo] + 2) / 3)
  
  # Converted: auto
  
  
  dimension: quarterno {
    type: number
    sql: NULL ;;
    
    label: "QuarterNo"
    
  }
  
  
  
  
  # Original DAX: YEAR([Date])
  
  # Converted: auto
  
  
  dimension: year {
    type: number
    sql: NULL ;;
    
    label: "Year"
    
  }
  
  
  
  dimension_group: date_field {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.Date ;;
    
    label: "Date"
    
  }
  
  
}