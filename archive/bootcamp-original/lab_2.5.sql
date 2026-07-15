#1 Select all the actors with the first name ‘Scarlett’.
SELECT actor_id , IF(first_name LIKE '%Scarlett%' , first_name, '') AS Scarlett FROM sakila.actor WHERE first_name LIKE '%Scarlett%';

#2 How many films (movies) are available for rent and how many films have been rented?
SELECT COUNT(*)
FROM `sakila`.`rental`
WHERE return_date IS NULL

SELECT COUNT(*)
FROM sakila.rental
WHERE return_date IS NOT NULL

#3 What are the shortest and longest movie duration? Name the values max_duration and min_duration.
SELECT min(length) as min_duration FROM sakila.film;
SELECT max(length) as max_duration FROM sakila.film;

#4 What's the average movie duration expressed in format (hours, minutes)?
select sec_to_time(avg(length)*60) from sakila.film;

#5 How many distinct (different) actors' last names are there?
select distinct last_name from sakila.actor 

#6 Since how many days has the company been operating (check DATEDIFF() function)?
SELECT DATEDIFF(max(rental_date),min(rental_date))
FROM sakila.rental;

#7 Show rental info with additional columns month and weekday. Get 20 results.
SELECT *, date_format(rental_date, "%M") as Month,
date_format(rental_date, "%W") as Weekday
FROM sakila.rental
limit 20

#8 Add an additional column day_type with values 'weekend' and 'workday' depending on the rental day of the week.
select *, case when date_format(rental_date, "%W") in ("saturday", "sunday") then "weekend"
else "workday"
end as day_type
from sakila.rental

#9 How many rentals were in the last month of activity?
SELECT COUNT(*) from sakila.payment where
(payment_date BETWEEN '2005-05-26'AND '2005-06-26')