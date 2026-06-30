select * from UNT_Bibliometrics.dbo.stg_openalex_authors

select * from UNT_Bibliometrics.dbo.stg_openalex_topics


select * from UNT_Bibliometrics.dbo.stg_openalex_works

select * from UNT_Bibliometrics.dbo.stg_unt_faculty


create view publication_volume_trend as
select publication_year, count(work_id) as total_works
from UNT_Bibliometrics.dbo.stg_openalex_works
group by publication_year 
order by publication_year


create or alter view domain_stats as
select domain_id, domain_name, count(distinct work_id) as total_works
from UNT_Bibliometrics.dbo.stg_openalex_topics
group by domain_name, domain_id
order by domain_id

select * from UNT_Bibliometrics.dbo.domain_stats


--	domains/1	Life Sciences	18720
--	domains/2	Social Sciences	44748
--	domains/3	Physical Sciences	52547
--	domains/4	Health Sciences	25596

create or alter view domain_field_stats as
select domain_id, domain_name, field_id, field_name, count(distinct work_id) as total_works
from UNT_Bibliometrics.dbo.stg_openalex_topics
group by domain_name, domain_id, field_id, field_name
order by domain_id, field_id

select sum(total_works) from UNT_Bibliometrics.dbo.domain_field_stats

--	
--	domains/1	Life Sciences	fields/11	Agricultural and Biological Sciences	3101
--	domains/1	Life Sciences	fields/13	Biochemistry, Genetics and Molecular Biology	9489
--	domains/1	Life Sciences	fields/24	Immunology and Microbiology	1071
--	domains/1	Life Sciences	fields/28	Neuroscience	4627
--	domains/1	Life Sciences	fields/30	Pharmacology, Toxicology and Pharmaceutics	432
--	domains/2	Social Sciences	fields/12	Arts and Humanities	4055
--	domains/2	Social Sciences	fields/14	Business, Management and Accounting	5659
--	domains/2	Social Sciences	fields/18	Decision Sciences	1985
--	domains/2	Social Sciences	fields/20	Economics, Econometrics and Finance	2604
--	domains/2	Social Sciences	fields/32	Psychology	11485
--	domains/2	Social Sciences	fields/33	Social Sciences	18960
--	domains/3	Physical Sciences	fields/15	Chemical Engineering	1074
--	domains/3	Physical Sciences	fields/16	Chemistry	4703
--	domains/3	Physical Sciences	fields/17	Computer Science	12392
--	domains/3	Physical Sciences	fields/19	Earth and Planetary Sciences	1002
--	domains/3	Physical Sciences	fields/21	Energy	673
--	domains/3	Physical Sciences	fields/22	Engineering	14512
--	domains/3	Physical Sciences	fields/23	Environmental Science	4921
--	domains/3	Physical Sciences	fields/25	Materials Science	7277
--	domains/3	Physical Sciences	fields/26	Mathematics	2663
--	domains/3	Physical Sciences	fields/31	Physics and Astronomy	3330
--	domains/4	Health Sciences	fields/27	Medicine	21223
--	domains/4	Health Sciences	fields/29	Nursing	316
--	domains/4	Health Sciences	fields/34	Veterinary	115
--	domains/4	Health Sciences	fields/35	Dentistry	166
--	domains/4	Health Sciences	fields/36	Health Professions	3776


create or alter view domain_field_subfield_stats as
select domain_id, domain_name, field_id, field_name, subfield_id, subfield_name, count(distinct work_id) as total_works
from UNT_Bibliometrics.dbo.stg_openalex_topics
group by domain_name, domain_id, field_id, field_name, subfield_id, subfield_name
order by domain_id, field_id, subfield_id 


create or alter view domain_field_subfieled_topic_stats as 
SELECT domain_id, domain_name, field_id, field_name, subfield_id, subfield_name, topic_id, topic_name, count(distinct work_id) as total_works
    FROM UNT_Bibliometrics.dbo.stg_openalex_topics 
    GROUP BY domain_name, domain_id, field_id, field_name, subfield_id, subfield_name, topic_id, topic_name
    order by domain_id, field_id, subfield_id, topic_id


WITH UniqueTopics AS (
    SELECT domain_id, domain_name, field_id, field_name, subfield_id, subfield_name, topic_id, topic_name, count(*) as total_works
    FROM UNT_Bibliometrics.dbo.stg_openalex_topics 
    GROUP BY domain_name, domain_id, field_id, field_name, subfield_id, subfield_name, topic_id, topic_name
)
SELECT COUNT(*) FROM UniqueTopics;

  -- 4081


select * from UNT_Bibliometrics.dbo.stg_openalex_works

create view open_access_stats as
select publication_year,
sum(case when is_oa = 1 then 1 else 0 end) as open_access_works,
(sum(case when is_oa = 1 then 1 else 0 end)  * 100.0 / count(*)) as open_access_percentage, 
sum(case when is_oa = 0 then 1 else 0 end) as closed_access_works,
(sum(case when is_oa = 0 then 1 else 0 end) * 100.0 / count(*)) as closed_access_percentage,
count(*) as total_works
from UNT_Bibliometrics.dbo.stg_openalex_works
group by publication_year
order by publication_year


create view total_open_access_stats as
select sum(open_access_works) as total_open_access_works, sum(closed_access_works) as total_closed_works, sum(open_access_works) * 100.0 / sum(total_works) as total_open_access_percentage, sum(closed_access_works) * 100.0 / sum(total_works) as total_closed_access_percentage
from UNT_Bibliometrics.dbo.open_access_stats

create view domain_citations as
select sot.domain_id, sot.domain_name, sot.field_id,sot.field_name,
sum(case when sow.cited_by_count between 0 and 10 then 1 else 0 end) as below_10_citations,
sum(case when sow.cited_by_count between 11 and 20 then 1 else 0 end) as below_20_citations,
sum(case when sow.cited_by_count between 21 and 30 then 1 else 0 end) as below_30_citations,
sum(case when sow.cited_by_count between 31 and 40 then 1 else 0 end) as below_40_citations,
sum(case when sow.cited_by_count between 41 and 50 then 1 else 0 end) as below_50_citations,
sum(case when sow.cited_by_count > 50 then 1 else 0 end) as above_50_citations
from UNT_Bibliometrics.dbo.stg_openalex_works sow join UNT_Bibliometrics.dbo.stg_openalex_topics sot on sow.work_id = sot.work_id
group by sot.domain_id, sot.domain_name, sot.field_id,sot.field_name
order by sot.domain_id, sot.field_id


create view work_type_stats as
select distinct(work_type), count(*) as total_works
from UNT_Bibliometrics.dbo.stg_openalex_works
group by work_type 


create view unt_affiliation_stats as
select sum(case when unt_affiliation_percentage between 0 and 20 then 1 else 0 end) as below_20_percent_unt_authors_works,
       sum(case when unt_affiliation_percentage between 21 and 40 then 1 else 0 end) as below_40_percent_unt_authors_works,
       sum(case when unt_affiliation_percentage between 41 and 60 then 1 else 0 end) as below_60_percent_unt_authors_works,
       sum(case when unt_affiliation_percentage between 61 and 80 then 1 else 0 end) as below_80_percent_unt_authors_works,
       sum(case when unt_affiliation_percentage between 81 and 99 then 1 else 0 end) as below_99_percent_unt_authors_works,
       sum(case when unt_affiliation_percentage = 100 then 1 else 0 end) as unt_authors_works
from (
select work_id,
	   sum(case when is_unt_affiliated =1 then 1 else 0 end) as unt_affiliations_count,
	   max(author_position) as total_authors,
       (sum(case when is_unt_affiliated = 1 then 1 else 0 end) * 100) / max(author_position) as unt_affiliation_percentage
from UNT_Bibliometrics.dbo.stg_openalex_authors
group by work_id
) as unt_affiliations


create view author_stats as 
select author_id,
    author_name, 
    count(distinct work_id) as total_unique_works
from unt_bibliometrics.dbo.stg_openalex_authors
where is_unt_affiliated = 1
group by author_name ,author_id
order by total_unique_works desc;

create view faculty_stats as 
select soa.author_id,soa.author_name, Max(suf.department) as Department, Max(suf.college) as College,  count(distinct soa.work_id) as total_unique_works
from UNT_Bibliometrics.dbo.stg_openalex_authors soa left join UNT_Bibliometrics.dbo.stg_unt_faculty suf on soa.author_name = suf.faculty_name 
where soa.is_unt_affiliated = 1
group by soa.author_name, soa.author_id
order by total_unique_works desc


create or alter view author_field_stats as
select soa.author_name, sot.domain_name, sot.field_name, sot.subfield_name,sot.topic_name, count(distinct soa.work_id ) as total_records
from UNT_Bibliometrics.dbo.stg_openalex_authors soa left join UNT_Bibliometrics.dbo.stg_openalex_topics sot on soa.work_id = sot.work_id 
where soa.is_unt_affiliated = 1
group by soa.author_name, sot.domain_name, sot.field_name, sot.subfield_name,sot.topic_name
order by total_records desc


create view unique_unt_authors as
select count(*) as unique_authors from (
select distinct author_name, author_id
from UNT_Bibliometrics.dbo.stg_openalex_authors
where is_unt_affiliated = 1) as unt_authors









