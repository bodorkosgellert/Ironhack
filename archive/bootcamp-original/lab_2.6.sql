#1 Get release years.
select * from film;
select distinct release_year from film

#2Get all films with ARMAGEDDON in the title.
select title from film 
where title like '%Armageddon%'

#3Get all films which title ends with APOLLO.
select title from film
where title LIKE '%apollo'

#4Get 10 the longest films.
select title from film
order by lenght desc
limit 10

#5How many films include Behind the Scenes content?
select count(*) from film
where special_features like '%behind the scenes%'

#6Drop column picture from staff.
select * from staff
alter table staff drop colummn picture

#7A new person is hired to help Jon. Her name is TAMMY SANDERS, and she is a customer. 
#Update the database accordingly.
select * from costumer
where first name = 'tammy' and last name = 'sanders'

insert into staff(first_name, last_name, email, address_id, store_id, username)
values('tammy','sanders','tammy.sanders@sakilacustomer.org', 79, 2, 'tammy')

#8Add rental for movie "Academy Dinosaur" by Charlotte Hunter from Mike Hillyer at Store 1. 
#You can use current date for the rental_date column in the rental table. 
#Hint: Check the columns in the table rental and see what information you would need to add there. 
#You can query those pieces of information. 
#For eg., you would notice that you need customer_id information as well. To get that you can use the following query:
#select customer_id from sakila.customer
#where first_name = 'CHARLOTTE' and last_name = 'HUNTER';
#Use similar method to get inventory_id, film_id, and staff_id.
select customer_id from customer where first_name = 'charlotte' and last_name = 'hunter'
select film_id from film where title = 'academy dinosaur'
select inventory_id from inventory where film_id = 1
select * from staff
select * from rental
insert into rental(rental_date, inventory_id, customer_id, staff_id)
values(curdate(), 1, 130, 1)


#9Delete non-active users, but first, create a backup table deleted_users to store customer_id, 
#email, and the date for the users that would be deleted. Follow these steps:
#Check if there are any non-active users
#Create a table backup table as suggested
#Insert the non active users in the table backup table
#Delete the non active users from the table customer
select * from customer

select * from customer where active = 0

drop table if exists deleted_users

create table deleted_user(
customer_id int unique not null,
email varchar(255) unique not null,
delete_date date)

insert into deleted_users
select customer_id, email, curdate()
from customer
where active = 0

select * from deleted_user
delete from customer where active = 0