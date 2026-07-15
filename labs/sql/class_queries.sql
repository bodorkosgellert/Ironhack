# 1. 	Write a SELECT statement that lists the customerid along 
#with their account number, type, the city the customer lives 
#in and their postalcode.

select * from address; # postal code and city
select * from costumer; #cust id and type and account
select * from customeraddress # joining fields cust id, addr id

select c.CustomerID, c.CustomerType, c.AccountNumber, a.City, a.PostalCode from customer c
join customeraddress ca using(CustomerID)
join address a using(AddressID);

# 2. Write a SELECT statement that lists the 20 most recently launched products, their name and colour
select Name, ProductNumber, Color from product
order by SellStartDate DESC
LIMIT 20;

#3. Write a SELECT statement that shows how many products 
#are on each shelf in 2/5/98 - group by + count distinct

select Shelf, count(distinct ProductID)
 from productinventory
 where ModifiedDate = '1998-05-02 00:00:00'
 group by Shelf;
 
 #4. I am trying to track down a vendor email address… his name is Stuart 
 #and he works at G&K Bicycle Corp. Can you help?
 
 select c.EmailAddress from contact c
 join vendorcontact vc using(ContactID)
 join vendor v using(VendorID)
 where c.FirstName = 'Stuart'
 and v.Name = 'G & K Bicycle Corp.';

 #5 What’s the total sales tax amount for sales to Germany? 
 #What’s the top region in Germany by sales tax?
 
select sp.Name as RegionRame, sum(s.TaxAmt) as taxtotal 
 from salesorderheader s # amount
 join salesterritory st using(TerritoryID) # country - filter
 join address a on s.BillToAddressID = a.AddressID # ship address - to get region
 join stateprovince sp using(StateProvinceID) # region
 where st.name = 'Germany'
 Group by sp.Name
 order by sum(s.TaxAmt) DESC
 LIMIT 1;
  
  
select table_name, column_name
from information_schema.columns
where table_schema ='adventureworks'
and column_name like '%tax%'

#6.	Summarise the distinct # transactions by month
select COUNT(*) FROM adventureworks.transactionhistory
group by MONTH(transactiondate)
 

#7.  Which ( if any) of the sales people exceeded their sales quota this year and last year?
select SalesPersonID, SalesQuota, SalesYTD, SalesLastYear from salesperson
where SalesYTD>SalesQuota AND SalesLastYear > SalesQuota

#8.  Do all products in the inventory have photos in the database and a text product description? 


#9.  What's the average unit price of each product name on purchase orders which were not fully, but at least partially rejected?
#10. How many engineers are on the employee list? Have they taken any sickleave?
SELECT COUNT(*) FROM adventureworks.employee
where Title like '%nginee%'

SELECT COUNT(*) FROM adventureworks.employee
where Title like '%nginee%'
and SickLeaveHours > 0
#11. How many days difference on average between the planned and actual end date of workorders in the painting stages?
