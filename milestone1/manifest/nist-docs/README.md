NIST Interoperability Site
==========================

This is a partial markdown conversion of the NIST site.
Hopefully it has all the relevant info for implementing ElectionGuard + Cardano.
I saved the PDFs locally but left other links as-is.

Share
-----

[Facebook](https://www.facebook.com/share.php?u=https://www.nist.gov/itl/voting/interoperability "Facebook")

[Linkedin](https://www.linkedin.com/shareArticle?mini=true&url=https://www.nist.gov/itl/voting/interoperability&source=https://www.nist.gov/itl/voting/interoperability "Linkedin")

[X.com](https://x.com/intent/tweet?url=https://www.nist.gov/itl/voting/interoperability&status=https://www.nist.gov/itl/voting/interoperability "X.com")

[Email](mailto:?subject=NIST.gov&body=Check%20out%20this%20site%20https://www.nist.gov/itl/voting/interoperability "Email")

**Overview** 
-------------

The essence of interoperability is to enable various devices to work together to perform common processes and achieve shared goals. To realize this capability in election technology, means taking steps toward creating a foundation that enables common data and processes to be carried out through the entire election eco-system. The NIST efforts in interoperability focus on Common Data Formats to allow election information to move between parts of the election eco-system.   

Common Data Formats (**CDFs)**
------------------------------

NIST has led the development of CDFs to support interoperability. The first 4 CDFs are called out in the VVSG. Going beyond the VVSG-required CDFs, additional formats were developed based on two studies which identified gaps remaining in election eco-system interoperability and strategies to address them. 

*   [Gap Analysis for Key Interoperability Scenarios in Election Technology](./NIST.GCR.22-033.pdf)
*   [Recommendations for Voting System Interoperability](./NIST.GCR.22-034.pdf)
     

| CDF Specification | Reference Implementation | Required in VVSG 2.0 |
| --- | --- | --- |
| [Voter Records Interchange](./NIST.SP.1500-102.pdf) | [https://github.com/usnistgov/VoterRecordsInterchange](https://github.com/usnistgov/VoterRecordsInterchange "https://github.com/usnistgov/VoterRecordsInterchange") (link is external)   | **Yes**  |
| [Cast Vote Records](NIST.SP.1500-103.pdf) | [https://github.com/usnistgov/CastVoteRecords](https://github.com/usnistgov/CastVoteRecords "https://github.com/usnistgov/CastVoteRecords") (link is external)   | **Yes**  |
| [Election Results](./NIST.SP.1500-100r2.pdf) | [https://github.com/usnistgov/ElectionResultsReporting](https://github.com/usnistgov/ElectionResultsReporting "https://github.com/usnistgov/ElectionResultsReporting") (link is external)   | **Yes**  |
| [Election Event Logging](./NIST.SP.1500-101.pdf) | [https://github.com/usnistgov/ElectionEventLogging](https://github.com/usnistgov/ElectionEventLogging "https://github.com/usnistgov/ElectionEventLogging") (link is external)   | **Yes**  |
| [Ballot Definition Specification](./NIST.SP.1500-20.pdf) | [https://github.com/usnistgov/BallotDefinition](https://github.com/usnistgov/BallotDefinition) (link is external) | **No** |
| [Micro-CDF Specification](./NIST.SP.1500-19.pdf) | [https://github.com/usnistgov/mcdf](https://github.com/usnistgov/mcdf) (link is external) | **No** |

Common Data Format Test Method
------------------------------

The CDF test method is a machine-executable method for testing voting CDFs. Its use is intended for voting system manufacturers, voting system test laboratories, and other members of the election community.

*   Find more information about the test method from the CDF test method GitHub site.
    *   [https://github.com/usnistgov/cdf-test-method](https://github.com/usnistgov/cdf-test-method "https://github.com/usnistgov/cdf-test-method") (link is external)
*   Download the test method from the releases page of the CDF test method GitHub site.
    *   [https://github.com/usnistgov/cdf-test-method/releases](https://github.com/usnistgov/cdf-test-method/releases "https://github.com/usnistgov/cdf-test-method/releases") (link is external)

CDF-Related Publications  
 
----------------------------

| Publication Date | Publication Type | Title |
| --- | --- | --- |
| 2024 | NIST GCR 24-058 | [Implementation Guidance for Common Data Formats](.//NIST.GCR.24-058.pdf) |
| 2022 | NIST GCR 22-034 | [Recommendations for Voting System Interoperability](./NIST.GCR.22-034.pdf) |
| 2022 | NIST GCR 22-033 | [Gap Analysis for Key Interoperability Scenarios in Election Technology](./NIST.GCR.22-033.pdf) |
| 04/2020 | NIST SP 1500-101 | [Election Event Logging Common Data Format Specification](./NIST.SP.1500-101.pdf) |
| 11/2019 | NIST SP 1500-102 | [Voter Records Interchange Common Data Format Specification](./NIST.SP.1500-102.pdf) |
| 11/2019 | NIST SP 1500-103 | [Cast Vote Records Common Data Format Specification](./NIST.SP.1500-103.pdf) |
| 2/2/2016 | NIST SP 1500-100 | [Election Results Common Data Format Specification](./NIST.SP.1500-100r2.pdf) |

Additional information can be found at the Interoperability GitHub site: [https://github.com/usnistgov/Voting](https://github.com/usnistgov/Voting "https://github.com/usnistgov/Voting") (link is external) 

**History** 
------------

NIST’s original involvement in carrying out this interoperability vision began with considerations of the need for common, non-proprietary formats for voting device interactions. Initial steps toward this idea (public format, import, export) were outlined in the original VVSG 2007 TGDC Recommendations. A larger community conversation followed in 2009, with the first NIST Common Data Format (CDF) workshop. The early days of this work involved some initial activities through working group efforts with IEEE. These efforts were eventually continued through NIST in the form of VVSG 2.0 public working groups. A number of VVSG 2.0 interoperability-specific working groups were formed to identify and prototype initial specifications and reference implementations for a set of common data formats that could cover the essential aspects of election processes. The activities in these groups focused mostly on organizing, modeling, and specifying knowledge about election processes and data. These efforts resulted in the creation of an initial set of CDFs whose draft specifications and reference implementations are located, respectively, in the NIST 1500 special publication series specifications and in related GitHub repositories (for reference UML models and XML/JSON implementations). The CDF specifications identified for inclusion in VVSG 2.0 were the Voter Records Interchange, Cast Vote Records, Election Results, and Election Event Logging specifications. Implementation and adoption of these CDFs through VVSG 2.0 will represent a major initial step toward realization of the interoperability vision. 

Following the release of VVSG 2.0, NIST continued its interoperability research using working groups to help develop the two additional CDFs. Information about the groups is available on the [History and Archive section](https://www.nist.gov/itl/voting/history-voting "History of Voting at NIST").

[Information technology](https://www.nist.gov/topic-terms/information-technology) and [Voting systems](https://www.nist.gov/topic-terms/voting-systems)

Created July 21, 2017, Updated November 15, 2024

[![National Institute of Standards and Technology logo](Interoperability%20_%20NIST_files/NIST-Logo-Brand-White.svg)](https://www.nist.gov/ "National Institute of Standards and Technology")

### HEADQUARTERS

100 Bureau Drive  
Gaithersburg, MD 20899  
[301-975-2000](tel:301-975-2000)

[Webmaster](mailto:do-webmaster@nist.gov) | [Contact Us](https://www.nist.gov/about-nist/contact-us) | [Our Other Offices](https://www.nist.gov/visit)

[X.com](https://x.com/NIST) [Facebook](https://www.facebook.com/NIST) [LinkedIn](https://www.linkedin.com/company/nist) [Instagram](https://www.instagram.com/nist/) [YouTube](https://www.youtube.com/NIST) [Giphy](https://giphy.com/nist) [RSS Feed](https://www.nist.gov/news-events/nist-rss-feeds) [Mailing List](https://public.govdelivery.com/accounts/USNIST/subscriber/new)

How are we doing? [Feedback](https://www.nist.gov/form/nist-gov-feedback?destination=/itl/voting/interoperability "Provide feedback")

*   [Site Privacy](https://www.nist.gov/privacy-policy)
*   [Accessibility](https://www.nist.gov/oism/accessibility)
*   [Privacy Program](https://www.nist.gov/privacy)
*   [Copyrights](https://www.nist.gov/oism/copyrights)
*   [Vulnerability Disclosure](https://www.commerce.gov/vulnerability-disclosure-policy)
*   [No Fear Act Policy](https://www.nist.gov/no-fear-act-policy)
*   [FOIA](https://www.nist.gov/office-director/freedom-information-act)
*   [Environmental Policy](https://www.nist.gov/environmental-policy-statement)
*   [Scientific Integrity](https://www.nist.gov/summary-report-scientific-integrity)
*   [Information Quality Standards](https://www.nist.gov/nist-information-quality-standards)
*   [Commerce.gov](https://www.commerce.gov/)
*   [Science.gov](http://www.science.gov/)
*   [USA.gov](http://www.usa.gov/)
*   [Vote.gov](https://vote.gov/)
