select * from UNT_Bibliometrics.dbo.stg_openalex_authors

select * from UNT_Bibliometrics.dbo.stg_openalex_topics

select * from UNT_Bibliometrics.dbo.stg_openalex_works

select * from UNT_Bibliometrics.dbo.stg_unt_faculty

-- Data Auditing

select count(*) from UNT_Bibliometrics.dbo.stg_openalex_authors
--359,947

select count(*) from UNT_Bibliometrics.dbo.stg_openalex_topics
--141.611

select count(*) from UNT_Bibliometrics.dbo.stg_openalex_works
--52,039

select count(*) from UNT_Bibliometrics.dbo.stg_unt_faculty
--1889


-- Authors - stg_openalex_authors

select count(*) as total_count,
	   sum(case when author_id is null then 1 else 0 end) as null_author_id,
	   sum(case when author_name is null then 1 else 0 end) as null_author_name,
	   sum(case when author_orcid is null then 1 else 0 end) as null_author_orcid,
	   sum(case when institution_id is null then 1 else 0 end) as null_institution_id,
	   sum(case when institution_name is null or institution_name = '' then 1 else 0 end) as null_institution_name,
	   sum(case when is_unt_affiliated is null then 1 else 0 end) as null_is_unt_affiliated
from UNT_Bibliometrics.dbo.stg_openalex_authors

    --359947	14425	0   122890	 27147	 27147  0

	-- The reason behind null values in the below columns
	--author_id NULL          - OpenAlex couldn't assign/disambiguate the author
	--author_orcid NULL       - very common, ORCID is voluntary and most researchers lack one
	--institution_id NULL     - author listed no affiliation, or OpenAlex failed to parse it
	--institution_name NULL   - same root cause as institution_id (they're set together)
	                          -- some records in institution_name are nul and blank

select (sum(case when author_id is null then 1.0 else 0 end) * 100 / count(*))
from UNT_Bibliometrics.dbo.stg_openalex_authors

-- 4.007534 percentage of authors has no insitution_id, institution_name


SELECT COUNT(*) as notuntworks
FROM (
    SELECT work_id
    FROM UNT_Bibliometrics.dbo.stg_openalex_authors
    GROUP BY work_id
    HAVING max(cast(is_unt_affiliated as int)) = 0
) AS notUntWorks;


	--W7130690074
	--W2592518050
	--W7163386725
	--W2098082628
	--W2752326209
	--W4400090125
	--W7140814073
	--W4411413853
	--W4402580595
	--W2128886090
	--W4406840771
	--W4393397025
	--W4403916463
	--W4366679995
	--W4360613813
	--W2916657809
	--W4415092555
	--W4241671649
	--W3125762857
	--W4410314789
	--W2920675743
	--W3108936441
	--W4411414167
	--W4234540164
	--W2747560345
	--W4223591189
	--W4415091769
	--W2043449557
	--W4206372994
	--W2163987497
	--W4405220977

	-- These are 31 works that doesn't have any author affiliated to unt
    -- I have indentified that these 31 records are actually unt affiliated.
    -- There were no unt_affiliated in the records because, there are more than 500+ authors in this work.
    -- Our python code only extracted top 100 position authors according to the paper, so it missed the unt_affiliated professors information.

select count(distinct work_id)
from stg_openalex_authors
where is_unt_affiliated = 1

	--52008 work records with atleast one author affiliated to UNT

select count(distinct work_id)
from stg_openalex_authors

	--52039 unique work records


SELECT 
    CASE 
        WHEN UntAuthorCount BETWEEN 1 AND 10 THEN '1 to 10 UNT authors'
        WHEN UntAuthorCount BETWEEN 11 AND 20 THEN '11 to 20 UNT authors'
        WHEN UntAuthorCount BETWEEN 21 AND 30 THEN '21 to 30 UNT authors' -- Filled the gap
        WHEN UntAuthorCount BETWEEN 31 AND 40 THEN '31 to 40 UNT authors'
        ELSE 'More than 40 UNT authors'
    END AS UNT_Author_Range,
    COUNT(*) AS Number_of_Works
FROM (
    SELECT 
        work_id, 
        COUNT(DISTINCT CASE WHEN is_unt_affiliated = 1 THEN author_id END) AS UntAuthorCount
    FROM UNT_Bibliometrics.dbo.stg_openalex_authors
    GROUP BY work_id
) AS WorkSummary
WHERE UntAuthorCount > 0 -- Only look at papers with at least 1 UNT author
GROUP BY 
    CASE 
        WHEN UntAuthorCount BETWEEN 1 AND 10 THEN '1 to 10 UNT authors'
        WHEN UntAuthorCount BETWEEN 11 AND 20 THEN '11 to 20 UNT authors'
        WHEN UntAuthorCount BETWEEN 21 AND 30 THEN '21 to 30 UNT authors'
        WHEN UntAuthorCount BETWEEN 31 AND 40 THEN '31 to 40 UNT authors'
        ELSE 'More than 40 UNT authors'
    END;


-- Topics - stg_openalex_topics

select count(*) as total_count,
	   sum(case when topic_id is null then 1 else 0 end) as null_topic_id,
	   sum(case when topic_name is null then 1 else 0 end) as null_topic_name,
	   sum(case when domain_id is null then 1 else 0 end) as null_domain_id,
	   sum(case when domain_name is null then 1 else 0 end) as null_domain_name,
	   sum(case when field_id is null then 1 else 0 end) as null_field_id,
	   sum(case when field_name is null then 1 else 0 end) as null_field_name,
	   sum(case when subfield_id is null then 1 else 0 end) as null_subfield_id,
	   sum(case when subfield_name is null then 1 else 0 end) as null_subfield_name
from UNT_Bibliometrics.dbo.stg_openalex_topics

	-- 141611	0	0	0	0	0	0	0	0
	--There are no null values in this table

-- Works - stg_openalex_works

select count(*) as total_count,
	   sum(case when work_id is null then 1 else 0 end) as null_work_id,
	   sum(case when doi is null then 1 else 0 end) as null_doi,
	   sum(case when title is null then 1 else 0 end) as null_title,
	   sum(case when publication_year is null then 1 else 0 end) as null_publication_year,
	   sum(case when publication_date is null then 1 else 0 end) as null_publication_date,
	   sum(case when work_type is null then 1 else 0 end) as null_work_type,
	   sum(case when is_oa is null then 1 else 0 end) as null_is_oa,
	   sum(case when oa_status is null then 1 else 0 end) as null_oa_status
from UNT_Bibliometrics.dbo.stg_openalex_works

	-- 52039	0	2497	0	0	0	0	0   0
	-- null_doi - 2497 suggets that doi data is missing in openalex platform


select count(work_id)
from stg_openalex_works
where work_id is null
	--0                    --This indicates there are no work_id nulls

select count(*)
from stg_openalex_works
group by work_id 
having count(*) > 1
	-- no data             --This indicates that there is no duplicate work_id in stg_openalex_works
	
	

select count(*) as total_count,
sum(case when oa_status = 'gold' then 1 else 0 end) as gold_counts,
sum(case when oa_status = 'hybrid' then 1 else 0 end) as hybrid_counts,
sum(case when oa_status = 'bronze' then 1 else 0 end) as bronze_counts,
sum(case when oa_status = 'green' then 1 else 0 end) as green_counts,
sum(case when oa_status = 'diamond' then 1 else 0 end) as diamond_counts,
sum(case when oa_status = 'closed' then 1 else 0 end) as closed_counts
from UNT_Bibliometrics.dbo.stg_openalex_works

	-- 52039	5850	2073	3611	6357	1888	32260

--The Six Open Access Categories
	--**gold**:The article is published in a fully open-access journal that is indexed by the Directory of Open Access Journals (DOAJ).
	--**hybrid**: The article is published in a traditional, toll-access (subscription) journal but is made freely available under an open license.
	--**bronze**: The article is free to read on the publisher's landing page, but it does not have a clearly identifiable open license (e.g., CC-BY).
	--**green**: The published version is behind a paywall, but a free version (such as a preprint or postprint) has been archived in an open access repository (like an institutional repository or PubMed Central).
	--*diamond**: If it is published in a fully open-access journal that charges no fees to anyone.
	--**closed**: If a research output does not fall into any of these categories and requires a paid subscription or login to read, its status is categorized as **closed**

select doi,title,count(*)
from stg_openalex_works
where doi is not null
group by doi,title
having count(*) > 1

	--  doi, title duplicates - 8 records are duplicates

	--  Titles
	--	Advanced modeling of materials with PAOFLOW 2.0: New features and software design - preprint & Article
	--	Secure Code Generation at Scale with Reflexion - both are articles - only difference is_oa column
	--	Achieving Unanimous Consensus Through Multi-Agent Deliberation - preprint & article
	--	Can X-Ray Observations Improve Optical-UV-based Accretion-rate Estimates for Quasars? - listed both of them as articles - but one of them is a preprint - arxiv
	--	Expand-and-Randomize: An Algebraic Approach to Secure Computation - preprint & article
	--	The rise of generative AI for metal-organic framework design and synthesis - identical records- only difference publication date
	--	The zero forcing numbers and propagation times of gear graphs and helm graphs - preprint & article
	--	Thermodynamic Formalism for Coarse Expanding Dynamical Systems - preprint & article

select doi,count(*)
from stg_openalex_works
where doi is not null
group by doi
having count(*) > 1


--doi duplicates - 28 records are duplicates
--I observed some of the records are preprints & articles

SELECT * 
FROM stg_openalex_works
WHERE doi IN (
    SELECT doi 
    FROM stg_openalex_works 
    GROUP BY doi 
    HAVING count(*) > 1
)
ORDER BY doi;

     -- I observed some records are identical - only \n in the title makes difference
     -- Some of the records names are trimmed, so there were duplicate records
     -- Some of them have different publication dates - with article, book-chapter, preprints 

select doi, work_type,count(*)
from stg_openalex_works
where doi is not null
group by doi, work_type
having count(*) > 1

select doi, venue_id ,count(*)
from stg_openalex_works
where doi is not null
group by doi, venue_id
having count(*) > 1

select doi, venue_id, work_type,count(*)
from stg_openalex_works
where doi is not null
group by doi, venue_id, work_type
having count(*) > 1

	--	https://doi.org/10.4324/9781003015024
	--	https://doi.org/10.1007/978-3-319-31075-6
	--	https://doi.org/10.1109/aiware69974.2025.00038
	--	https://doi.org/10.48550/arxiv.1102.1178
	--	https://doi.org/10.48550/arxiv.1109.5260
	--	https://doi.org/10.1016/j.matt.2026.102748
    --  These records are duplicates 



SELECT COUNT(*) AS total_duplicate_titles
FROM (
    SELECT title 
    FROM stg_openalex_works 
    GROUP BY title 
    HAVING COUNT(*) > 1
) AS duplicate_groups;

select *
FROM UNT_Bibliometrics.dbo.stg_openalex_works
where title in(
select title
from stg_openalex_works
group by title
having count(*) > 1)
order by title

--title duplicates - 1388 records are duplicates
-- Some of them are preprints & articles
-- we can remove some of the records that has null values in venue_name, venue_id, venuw_issn
-- we can remove some records where publication date is older keeping the newer one


-- UNT Faculty - stg_unt_faculty

select count(*),
	   sum(case when faculty_name is null then 1 else 0 end) as null_faculty_name,
	   sum(case when title is null then 1 else 0 end) as null_title,
	   sum(case when department is null then 1 else 0 end) as null_department,
	   sum(case when college is null then 1 else 0 end) as null_college,
	   sum(case when email is null then 1 else 0 end) as null_email
from UNT_Bibliometrics.dbo.stg_unt_faculty

	-- 1889	0	0	0	0	0
	-- This indicates that there are no null values in this table






-- Data Cleansing (To Make Data Consistent)

 -- First I am starting with Title 
 -- There are 1388 duplicate title records


WITH CTE_Duplicates AS (
    SELECT 
        title,
        ROW_NUMBER() OVER (
            PARTITION BY title 
            ORDER BY publication_date asc
        ) AS row_num
    FROM stg_openalex_works
    WHERE title IS NOT NULL
)
DELETE FROM CTE_Duplicates
WHERE row_num > 1;

 -- I am removing the newer data records keeping the oldest one

 -- Next I am working on doi duplicates

WITH CTE_Duplicates AS (
    SELECT 
        doi,
        ROW_NUMBER() OVER (
            PARTITION BY doi
            ORDER BY publication_date asc
        ) AS row_num
    FROM stg_openalex_works
    WHERE doi IS NOT NULL
)
DELETE FROM CTE_Duplicates
WHERE row_num > 1;

-- These removes duplicate doi records

 -- NOw I am removing the 31 records with no unt affiliation
delete from UNT_Bibliometrics.dbo.stg_openalex_authors
where work_id in (
    SELECT work_id
    FROM UNT_Bibliometrics.dbo.stg_openalex_authors
    GROUP BY work_id
    HAVING max(cast(is_unt_affiliated as int)) = 0
)

 -- 31 records were deleted

-- after preprocessing

select count(*) from UNT_Bibliometrics.dbo.stg_openalex_authors
--359,947 -- 355,200 now -- 4747 records are removed

select count(*) from UNT_Bibliometrics.dbo.stg_openalex_topics
--141.611

select count(*) from UNT_Bibliometrics.dbo.stg_openalex_works
--52,039 --49,971 now -- 2068 records are removed
select (52039 - 49971)

select count(*) from UNT_Bibliometrics.dbo.stg_unt_faculty
--1889








