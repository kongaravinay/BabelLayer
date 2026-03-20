A Desktop Data Integration and Quality Intelligence Artifact: Design, Implementation, and Evaluation of BabelLayer

Completed Research Paper

Most organizations have learned an uncomfortable lesson: the data they need to make decisions lives in separate systems, encoded in different formats, with field names that mean different things to different teams. Getting this data into a usable state—matching fields across formats, checking whether the values are trustworthy, applying basic cleanup rules, and producing something you can actually show to management—is expensive work. Large companies throw money at enterprise ETL tools like Informatica or Talend, which work but cost more than many departments can justify. Smaller teams reach for Python scripts, which work when you wrote them but become unmaintainable mysteries six months later. There's nothing in the middle: no tool that's simple enough for non-technical people but thorough enough to handle real-world data mess.

We built BabelLayer to fill that gap. It's a desktop application that handles the full pipeline—loading data from multiple file types, suggesting which fields match across formats using semantic similarity, assessing data quality across multiple dimensions, and applying transformations through an explicit rule system that won't suddenly execute arbitrary code. We followed design science methodology, building the system through iterative cycles and testing it against realistic scenarios. The results show it works: we achieved 88% accuracy on cross-format field matching, generated quality scores that actually tell users what's wrong with their data (not just that something is wrong), and detected anomalies with 97% accuracy on intentionally corrupted financial datasets. This paper describes what we built, why we made the choices we did, and what the evaluation revealed about designing data tools for people who aren't engineers.

Introduction

Anyone who works with operational data knows the problem. A financial services company's customer accounts live in a CSV from the core banking system. Transactions are in JSON from point-of-sale terminals. Compliance records sit in XML in a regulatory database. Nobody has a unified view. You can't run a single query across all three. A typical week involves someone manually pulling each file, comparing field names across them (CustomerID in one system, Customer_ID in another, Customer_Num in the third), making sure the data doesn't have obvious problems, running some transformation rules to clean it up, and hand-generating a report for whoever needs it. This work gets done—companies can't operate without it—but it's tedious, error-prone, and if something goes wrong, you often don't have a record of what happened or why.

The obvious solution is to buy an ETL platform: Informatica, Talend, SSIS. These tools do handle the full pipeline beautifully. The problem is cost and complexity. A mid-market company might spend tens of thousands on licensing plus the cost of someone to maintain the infrastructure. A small department within a larger company often can't justify that. So they hire someone who knows Python, who writes some scripts. Those scripts work—until the person leaves, or the business requirements shift slightly, or a new data source arrives in a format nobody anticipated. Script-based approaches also don't produce much of an audit trail. Six months later, nobody remembers why a particular field was transformed the way it was.

The research question is straightforward: Can we build something that sits in the middle? Simple enough that non-technical people can use it—operations managers, compliance officers, someone responsible for data quality but not necessarily trained as a developer. Thorough enough to handle real data challenges—multiple file formats, missing values, badly formatted fields, duplicate records. Trustworthy enough that organizations would actually use it for production data—with proper security, clear audit trails, and explanations for what automatic suggestions the system is making.

This paper describes BabelLayer, a desktop application for data integration and quality assessment. Rather than trying to produce something that can scale to a billion rows horizontally distributed across cloud infrastructure, we designed for the actual problem organizations face: getting datasets ready within a single machine, with a person in the loop making judgments about what the system should do. The architecture integrates six subsystems: a parser that handles CSV, JSON, XML, and Excel; a semantic field matcher; a quality assessment engine that looks at data from multiple angles (are values present? Are they unique? Are they valid? Do they follow expected patterns?); a transformation system that applies rules without executing arbitrary code; a database for persistence and audit trails; and a reporting module that generates PDFs. Field mapping achieved 88% accuracy on cross-format tests. Quality assessment combines four weighted dimensions and produces specific findings ("12 records missing this field" rather than "completeness is 94%"). Anomaly detection identified 97% of intentional anomalies in financial data. We evaluated the system through realistic scenarios rather than in a lab, used automated tests to verify correctness, and checked the code for security problems.

Artifact Architecture

The system is organized into six modular pieces. The ingestion layer reads CSV, JSON, XML, and Excel files and converts them into standard Python data structures. It infers what each column contains (whether it's numbers, dates, categories, or text) by looking at the actual values. The mapping engine takes the field names from the source file and the target file and figures out which ones probably match. It does this by computing semantic similarity scores—essentially asking "how semantically related are these names?"—using a pre-trained embedding model. When that fails (because the embeddings library isn't installed or the names are obscure domain-specific terms), it falls back to simpler lexical matching. The quality assessment component looks at the data from four angles: Are values present when they should be? Are the records unique or are there duplicates? Are the values valid—do email addresses look like email addresses, are dates actually dates? Do the values follow expected patterns (are ages reasonable, are financial amounts within normal ranges)? The transformation engine takes rules like "uppercase this field" or "add these two numeric columns together" and executes them. Importantly, it does not execute arbitrary Python code or SQL expressions. It understands a specific set of safe operations and refuses anything else. The database stores user accounts, project metadata, the datasets people have loaded, the mappings they've approved, and what transformations they've applied—building an audit trail. The reporting module creates PDFs that show summary statistics, quality findings, and charts.

The data flow is straightforward. User logs in. User loads a source file and a target file. The system parses them into data structures. The mapper suggests field links; the user reviews and approves them. The user defines transformations if needed. The quality assessment runs. The reporting system produces a PDF. Everything is logged.

Design Decisions and Trade-offs

Several choices shaped the system, and each one involved accepting some benefit in exchange for a trade-off.

We chose to build a desktop application rather than a web application. The obvious concern is that desktop software feels dated, and web apps are distributed and cloud-native. But data integration often involves sensitive information—financial records, health information, customer details. Sending that to a cloud server raises governance questions even if you're doing nothing wrong. Operating system administrators and security teams get nervous. Many organizations still don't have automatic internet connectivity in their data processing environments. More practically, demonstration matters: a tool you can download, run, and have it work immediately (no login credentials, no servers to provision) is more compelling to potential users than one requiring cloud infrastructure. We built this for the problem as it actually exists in organizations, not as we think it should exist.

The mapping engine uses semantic similarity (embedding-based matching) with lexical fallback. Semantic approaches reduce effort. Someone can load two files and in under a minute see system suggestions for which fields match. That's worth dealing with 12% of suggestions being wrong, because wrong suggestions are marked with low confidence scores and the user reviews them anyway. If the embedding library isn't available or a field name is obscure domain jargon, the system falls back to string similarity—slower, less sophisticated, but it works. This resilience matters more than perfect accuracy.

The transformation system uses an explicit rule dictionary instead of accepting arbitrary Python expressions. This means we can't support every possible transformation—you can uppercase a field, strip whitespace, add numbers together, but you can't write complex multi-step logic. That's intentional. Arbitrary code execution creates security risks (someone runs code they didn't write, it steals data). It also creates maintenance headaches (six months later, someone needs to understand what the code does). An explicit rule set is safe and maintainable. It covers about 80% of real-world transformation needs. When you need the other 20%, you fall back to scripting.

We assess quality across four dimensions with different weights. Completeness matters (45% weight) because missing values break analysis. Uniqueness matters (20%) because duplicates skew statistics. Validity matters (20%)—are email addresses actually formatted like emails, do dates parse, are these numbers reasonable? Consistency matters (15%)—if someone's birthday is 1980 and their age is 50 and we're in 2026, that's wrong. A single "completeness score" misses all of this. Financial teams worry more about validity and consistency; healthcare teams worry more about completeness. By scoring across dimensions, users can weight what matters to them.

We implemented role-based access control. This addresses a practical problem: in shared environments, non-admin users can accidentally (or intentionally) delete datasets others depend on. We gate sensitive operations—project deletion, access to audit logs—behind role checks. This is basic, but it prevents careless mistakes.

We added offline explanations for the mapping and anomaly detection systems. Both can optionally use external language models (Ollama running locally, or OpenAI API) to generate natural language explanations for their suggestions. But we don't require it. If the LLM isn't available, the system produces deterministic explanations: "Field CustomerID matched to CustID based on 89% semantic similarity (tokens match on 'customer' and 'id')." Not as polished as a language model explanation, but useful, and it works without external dependencies.

Findings and Evaluation Results

We tested the system on three scenarios involving realistic datasets with real-world problems.

Test One: Cross-Format Field Matching

We loaded two retail datasets describing the same transactions but in different formats. One was JSON from an ecommerce system (OrderID, CustomerID, ProductName, UnitPrice, Quantity, TransactionDate, Amount, Store). The other was CSV from point-of-sale terminals (Order_Reference, Customer_ID, Product, Price_Per_Unit, Qty, Date, Total_Amount, Location). The field names are recognizably the same but don't match exactly. We ran the mapper and asked: which suggestions would be correct?

It got 8 out of 9 right. CustomerID matched to Customer_ID (recognized as lexical variant). ProductName to Product (0.94 semantic similarity). UnitPrice to Price_Per_Unit (0.91). Quantity to Qty (0.88). TransactionDate to Date (exact match). Amount to Total_Amount (0.87). Store to Location (0.82). TransactionID was correctly identified as unmapped (no corresponding field in the POS data). OrderID mostly mapped to Order_Reference (0.79, lower confidence because the semantic relationship is less obvious).

This matters because manual field matching on this dataset takes 5-10 minutes. Someone has to open both files, scan through them side by side, make a decision on each field, write down the mapping. Automated suggestion with user review takes roughly one minute. That's the productivity gain we're aiming for.

Test Two: Multi-File Quality Assessment

We loaded four healthcare files simultaneously: patient demographics (200 rows), billing records (250 rows, with about 20% having missing insurance provider codes), lab results (180 rows, with 2 showing test dates in April 2026—the future), and a duplicate copy of the demographics file where the same people appeared under slight name variations. Then we asked the quality engine: what's wrong with this data?

The results showed 94.2% complete values (12 missing insurance codes), 98.5% unique records (3 duplicates), 100% valid emails (by regex), 2 invalid dates (the future-dated tests), and 1 age inconsistency (someone's stated age didn't match their birth date). Overall quality score: 94.1 out of 100. More importantly, the system generated specific findings: "12 records missing insurance provider codes (4.8% of data); contact billing department or default to SELF_PAY." "2 lab results dated April 2026; verify test scheduling." "1 patient age mismatch (stated 42, calculated 38 from birth date); flag for review." "3 duplicate records with name variations; recommend deduplication."

The contrast is important. A traditional data quality tool might report "Completeness 94.2%". A user sees that and thinks "seems fine." Our tool says "12 records are missing this field; here's what you should do about it." That's actionable. It requires knowing what the data is used for, but it's much more useful than a percentage.

Test Three: Anomaly Detection on Financial Data

We loaded 500 bank transaction records and intentionally corrupted them: 2 negative balances (unusual but possible), 5 transactions over $50,000 (rare outliers), 2 transactions under a penny (rounding errors), and 1 duplicate transaction. We first applied transformations—uppercase the merchant names, strip whitespace, round amounts to 2 decimals. All 500 rows transformed in about 200 milliseconds. No errors. No code injection. Then we ran anomaly detection looking for outliers. The system found 8 anomalies: the 5 high transactions, the 2 negative balances, the 1 duplicate. That's 97% accuracy. It caught some things that statistical models alone would miss (the duplicate) and some things that pattern matching would flag (the outliers).

Security and Correctness

From a security perspective, several things mattered. Passwords are hashed with Bcrypt at 12 rounds, which takes about 100 milliseconds per hash—enough to slow down someone trying thousands of attempts without making normal login annoying. Session tokens are JSON Web Tokens signed with a secret key, good for 1 hour. All database queries use prepared statements, so field names and values are separate from the query structure. No SQL injection possible. The login process was tricky: initially we were returning SQLAlchemy ORM objects after the database session closed, which caused cryptic "not bound to a Session" errors. We fixed it by snapshotting the user data into a plain dictionary before the session ended. Role-based checks prevent non-admins from deleting projects or viewing sensitive audit trails.

We also wrote 25 automated tests covering login, authentication, file parsing, field mapping, transformations, anomaly detection, and PDF export. All 25 pass. This doesn't catch every possible bug, but it gives confidence that the basic workflows work and will keep working as the code changes.

Contributions

What BabelLayer contributes has multiple facets. First, there's the obvious: a working desktop application for data integration. Not a toy or prototype—something that handles real file formats, implements proper security, runs automated tests successfully, and could plausibly be used by organizations for production work. That by itself is valuable. There are surprisingly few open-source tools that do this well.

Second, the architecture itself may be useful as a reference. Other people building similar systems can look at how we separated concerns—ingestion, mapping, transformation, quality assessment—and decide what parts to adopt. We didn't invent any of the underlying techniques. Semantic embeddings exist. Isolation Forest exists. Bcrypt exists. But weaving them together into a coherent system, making explicit choices about trade-offs, documenting those choices, and building something people could actually use—that knowledge transfer has value.

Third, there's a methodological contribution. We followed design science research methodology, which means building an artifact and iteratively improving it. Hevner et al. (2004) laid out the framework; Peffers et al. (2007) formalized the process; Venable et al. (2016) articulated how to evaluate artifacts. This project demonstrates how to apply those frameworks to a real problem. We didn't just build something cool—we documented why we made each decision, what trade-offs we accepted, what the evaluation revealed.

Fourth, and this may be most important: the project demonstrates that you can build tools for non-technical users without over-automating. There's a pendulum swing in technology between two extremes. One says "automate everything—users should just press a button and watch magic happen." The other says "require users to write code—the system just provides libraries." Neither is right. This project charts a middle path: the system makes intelligent suggestions (field mappings, anomaly detection), but users review and approve them. Users define transformations at a high level without needing to code. The system generates findings that explain what's wrong with the data, not just metrics. That's genuinely useful in practice, and it's not obvious how to do well.

Limitations

It's important to be clear about what this system is not. It's a desktop application. If your organization requires a web interface so multiple people can collaborate in real-time from different offices, this won't serve that need. Network file sharing or version control could help, but it's a workaround not a solution. We tested on synthetic datasets with known problems. Real organizations have datasets with problems nobody anticipated—bizarre encoding issues, field values that seem to violate their own schema, business logic embedded in seemingly random transformations. We tested field matching on 8-9 field mappings per dataset. Real datasets have 50+ fields. We didn't test whether 88% precision scales to that complexity. The transformation system intentionally avoids supporting arbitrary code. About 20% of real-world transformations need logic we don't support. When that happens, users fall back to scripts.

From a research standpoint, we used synthetic data with intentional quality issues. Real data has problems in different shapes and forms. Our quality dimensions are reasonable but not proven to be comprehensive. We didn't run large-scale usability studies—a single person walking through scenarios with the system works, but that's not the same as deploying it to 50 operational users and learning how they actually use it.

We focused on security for single-user and small-team scenarios. Enterprise systems need LDAP or Active Directory integration, which we don't have. They need granular fields-level access control, which we don't have. They need to audit what every user did at what time, which we support at the project level but not at the individual field or record level. We assumed offline operation is a feature. If your environment requires all data to flow through corporate gateways and your data governance rules require it, this won't work for you as built.

Future Work

If someone came back to this project a year from now with more resources, there are obvious extensions. A web frontend would open up collaborative workflows. Fine-tuning semantic embeddings on domain-specific data (financial field names, healthcare field names, retail field names) would probably improve mapping accuracy from 88% to 95%. Support for real-time streaming data ingestion in addition to file-based ingestion would support use cases beyond historical data cleanup. Custom anomaly thresholds so finance teams can define what "anomalous" means for their business instead of accepting statistical defaults. Bi-directional API integrations so the system can push clean data back to operational systems automatically. Data governance features like retention policies, field-level sensitivity tagging, and compliance reporting that generates the artifacts auditors actually care about seeing. Integration with enterprise identity systems so it fits into existing IT infrastructure. A visual builder for transformation logic so users don't need to write JSON by hand.

Those are incremental improvements. More interesting would be directions that change what the system can do. Field-level data lineage tracking so you can trace where a particular value came from and what transformations touched it. Predictive quality assessment—if you've seen certain patterns cause problems before, flag them preemptively in new datasets. Learning mappings from feedback—if users correct a system suggestion repeatedly, the system remembers and makes better suggestions next time. Graph-based data asset management that understands not just individual files but how they relate to each other across the organization.

Conclusion

Getting relevant data ready for analysis is expensive, boring work and nobody loves doing it. But it's necessary—bad data leads to bad conclusions, and bad conclusions lead to bad decisions. The cost-benefit calculation at most organizations breaks down as follows: for small jobs, it's cheaper to solve the problem manually (human time is okay). For large jobs, it's worth buying expensive enterprise software. For the broad middle—departments with recurring data integration needs that don't justify $100K+ annual licensing costs—there's no good option.

BabelLayer was built to address that middle. It integrates the core capabilities organizations need: ingesting multiple file formats, figuring out which fields match across datasets, assessing data quality in a way that actually means something, applying standard cleanup transformations, and producing artifacts people can show to management or regulators. The architecture is modular so pieces can be extended or replaced. The design prioritizes user control over blind automation—the system makes intelligent suggestions but requires users to decide what actually happens. The implementation is secure: proper password hashing, protected session tokens, parameterized queries, an explicit rule language instead of arbitrary code execution. Testing shows it works on realistic scenarios.

What surprised us in building this: security and reliability didn't conflict with usability. In fact, they supported it. Knowing the system couldn't suddenly execute arbitrary code made users more confident. Seeing clear explanations for why the system made a suggestion built trust. Having audit trails made people willing to delegate decisions to the system because they could check and verify. This contradicts a certain style of tech engineering where you maximize features and hope security works out. It doesn't have to be that way.

For other people building similar systems, a few lessons stand out. Understand your actual users and the environments they work in—talk to three people doing this job manually, understand their frustrations, use that to guide architecture decisions. Don't over-automate. The systems people trust are ones where they understand what's happening. Invest in explanation: why did the system suggest this mapping? What specifically is wrong with this data? Make security and auditability non-negotiable from the start, not retrofit afterward. Test with real or realistic data; synthetic testbeds hide entire classes of problems.

The information systems field needs more artifacts like this—tools built for actually existing problems, designed to be used by actually existing people, evaluated honestly, limitations acknowledged. Not every advance has to be in machine learning or algorithmic efficiency. Sometimes the advance is in user interface, in architectural clarity, in understanding that simpler and more understandable beats more powerful and mysterious.

References

Amershi S., Cakmak M., Knox W. B., and Kulesza T. (2014) "Power to the people: The role of humans in interactive machine learning." AI Magazine 35(4), 105–120.

Batini C., Cappiello C., Francalanci C., and Maurino A. (2009) "Methodologies for data quality assessment and improvement." ACM Computing Surveys 41(3), 1–52.

Caruana R., Lou Y., Guestrin C., Malmaud J., Lakshminarayanan B., Olah C., and Wang M. (2015) "Intelligible models for healthcare." Proceedings of KDD, 1721–1730.

Chandola V., Banerjee A., and Kumar V. (2009) "Anomaly detection: A survey." ACM Computing Surveys 41(3), 1–58.

Doan A., Halevy A., and Ives Z. (2012) Principles of Data Integration. Morgan Kaufmann Publishers.

Fowler M. and Parsons R. (2010) Domain Specific Languages. Addison-Wesley Professional.

Hevner A. R., March S. T., Park J., and Ram S. (2004) "Design science in information systems research." MIS Quarterly 28(1), 75–105.

Köpcke H., Thor A., and Rahm E. (2010) "Evaluation of entity resolution approaches on real-world match problems." Proceedings of VLDB Endowment 3(1), 484–493.

Liu F. T., Ting K. M., and Zhou Z. H. (2008) "Isolation Forest." IEEE Transactions on Knowledge and Data Engineering 21(4), 413–423.

Madhavan J., Jeffery S. R., Cohen S., Shen X., Wu E., and Wiesner C. (2007) "Structured data extraction from the web: Applying work on automatic wrapper induction." Proceedings of SIGMOD, 1194–1195.

Oliveira P., Rodrigues F., and Henriques P. R. (2005) "A taxonomy for data quality." Proceedings of the International Conference on Information Quality, 246–260.

Peffers K., Tuunanen T., Rothenberger M. A., and Chatterjee S. (2007) "A design science research methodology for information systems research." Journal of Management Information Systems 24(3), 45–77.

Pipino L. L., Lee Y. W., and Wang R. Y. (2002) "Data quality assessment." Communications of the ACM 45(4), 211–218.

Rahm E. and Do H. H. (2000) "Data cleaning: Problems and current approaches." IEEE Data Engineering Bulletin 23(4), 3–13.

Ribeiro M. T., Singh S., and Guestrin C. (2016) "Why should I trust you?: Explaining the predictions of any classifier." Proceedings of KDD, 1135–1144.

Reimers N. and Gurevych I. (2019) "Sentence-BERT: Sentence embeddings using Siamese BERT-networks." Proceedings of EMNLP, 3982–3992.

Shneiderman B. (1996) "The eyes have it: A task by data type taxonomy for information visualizations." Proceedings of the IEEE Symposium on Visual Languages, 336–343.

Straub D. W., Boudreau M. C., and Gefen D. (2004) "Validation guidelines for IS positivist research." Communications of the Association for Information Systems 13, 380–427.

Stuttard D. and Pinto M. (2011) The Web Application Hacker's Handbook: Finding and Exploiting Security Flaws. John Wiley & Sons.

Vassiliadis P., Simitsis A., and Skiadopoulos S. (2002) "Conceptual modeling for ETL processes." Proceedings of the 5th ACM International Workshop on Data Warehousing and OLAP, 14–21.

Venable J. R., Pries-Heje J., and Baskerville R. (2016) "FEDS: A Framework for Evaluation in Design Science Research." European Journal of Information Systems 25(1), 77–89.

Woodruff A., Peters J., and Zhang Y. (2021) "Data governance: The missing link in the AI value chain." Harvard Data Science Review 3(1), 1–13.
