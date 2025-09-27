


user request to and endpoint /health?store_id=123456

will check for the path get it this time -> "health"
will check also for the query param store_id -> "123456"

check if there is a key on redis present still {store_id}_{path}

if no create it:
    then use this value to save something on redis that has TTL of 30mins

    value should be an object like this: 
    { 
        'api-remaining-request': 4,
        'api-requests-reset': utc from the time of creation + 30mins
    }

if yes:
    check first if the rate-limit value is 0 then raise an error

    else:
        update the value of api-remaining-request
