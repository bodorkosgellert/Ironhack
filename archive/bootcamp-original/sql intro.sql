#Review the tables in the database.
#Explore tables by selecting all columns from each table or using the in built review features for your client.
#Select one column from a table. Get film titles.
SELECT title
FROM `sakila`.`film`;

#Select one column from a table and alias it. Get unique list of film languages under the alias language. Note that we are not asking you to obtain the language per each film, but this is a good time to think about how you might get that information in the future.
SELECT language_id as languages
FROM `sakila`.`film`;

#5.1 Find out how many stores does the company have?
SELECT store_id
FROM `sakila`.`store` 
order by store_id desc;

#5.2 Find out how many employees staff does the company have?
SELECT staff_id
FROM `sakila`.`staff`;
order by staff_id desc;

#5.3 Return a list of employee first names only?
SELECT first_name
FROM `sakila`.`staff`;
