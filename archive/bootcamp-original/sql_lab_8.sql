# 1Use the RANK() and the table of your choice rank films by length 
# (filter out the rows that have nulls or 0s in length column). 
# In your output, only select the columns title, length, and the rank.

select * ,
rank() over (order by length desc) as ranks
from sakila.film
where length is not null and length > 0;


# 2Build on top of the previous query and rank films by length within the rating category 
# (filter out the rows that have nulls or 0s in length column). 
# In your output, only select the columns title, length, rating and the rank.
select * ,
rank() over (partition by rating order by length desc) as ranks
from sakila.film
where length is not null and length > 0;


# 3How many films are there for each of the categories? 
# Inspect the database structure and use appropriate join to write this query.

select * , count(*) from sakila.category
inner join sakila.film_category using (category_id)
group by name

# 4Which actor has appeared in the most films?

select actor_id, count(*) as films from sakila.film_actor 
group by actor_id 
order by films desc

# 5Most active customer (the customer that has rented the most number of films)

select customer_id, count(*) as rental_amount from sakila.rental 
group by customer_id
order by rental_amount desc

