* Table Url:
    * id (pk)
    * group url/searchterm (if string includes space then it includes searchterm else url)
    * status

* Table config:
    * id (pk)
    * url id (fk)
    
    * xpath dict {
                  page:{'field_name_1':xpath
                  'field_name_2':xpath
                  'field_name_3':xpath
                 }
    * Exception
-------------------------------------------------

* Table Meetup_group:
    * id (pk)
    * config_id (FK)
    * name
    * location
    * no of members
    * Organizer url
    * Organizer name
    * about

* Table Members:
    * id (PK)
    * group_id (FK)
    * name
    * Location
    * Member since
    * introduction
    * profile pic (file path)
    * interests
    * group links list. (comma separated)
    * is_organizer
    * profile url

* Table event:
    * id
    * group_id (FK)
    * Event datetime
    * Event title
    * member attends (member ids) (FK)
    * event type (past/upcomming)
    * details

* Table Sponsors:
    * id
    * Event id (fk)
    * name
    * url

* Table Comment :
    * id
    * event id (fk)
    * member url   
    * comment
    * date time 

* Table Discussion:
    * id
    * group_id (FK)
    * member (FK)
    * comment

* Table Reply:
    * id
    * Discussion_id (fk)
    * member (fk)
    * comment

* Table member_attends_event
    * attendence_id
    * event_id
    * group_id