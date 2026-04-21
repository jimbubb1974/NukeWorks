  Research Spec

  # NukeWorks Research Data Capture Spec

  ## 1. Output Contract
  Return a single JSON object that matches this high-level structure:
  ```json
  {
    "metadata": { ... },
    "entities": {
      "technology_vendors": [ ... ],
      "products": [ ... ],
      "owners_developers": [ ... ],
      "constructors": [ ... ],
      "operators": [ ... ],
      "offtakers": [ ... ],
      "projects": [ ... ],
      "personnel": [ ... ]
    },
    "relationships": {
      "vendor_supplier_relationships": [ ... ],
      "owner_vendor_relationships": [ ... ],
      "project_vendor_relationships": [ ... ],
      "project_constructor_relationships": [ ... ],
      "project_operator_relationships": [ ... ],
      "project_owner_relationships": [ ... ],
      "project_offtaker_relationships": [ ... ],
      "vendor_preferred_constructor": [ ... ],
      "personnel_entity_relationships": [ ... ]
    }
  }

  All arrays are optional; omit an array if you found nothing for that
  collection. When a value is unknown or not public, use null rather than
  guessing.

  ## 2. Metadata Block

  ## 3. Entity Collections

  Each entity object must include a stable slug so the import script can upsert
  safely. Slugs should be lowercase, words separated by hyphens, and globally
  unique. Use sources to cite supporting URLs (full HTTP(S) links).

  ### 3.1 technology_vendors

  | Field | Required | Type | Guidance |
  | --- | --- | --- | --- |
  | slug | yes | string | e.g., "nuscale-power". |
  | notes | no | string | Key facts or context (notes). |
  | sources | yes | array of strings | URLs supporting the data. |

  ### 3.2 products

  | Field | Required | Type | Guidance |
  | slug | yes | string | Include vendor prefix, e.g., "nuscale-smr". |
  | vendor_slug | yes | string | Link to technology_vendors.slug. |
  | product_name | yes | string | (product_name). |
  | reactor_type | no | string | Use values like PWR, SMR, MSR when applicable.
  |
  | generation | no | string | e.g., III+. |
  | thermal_capacity | no | number | MW thermal (thermal_capacity). |
  | gross_capacity_mwt | no | number | If available. |
  | thermal_efficiency | no | number | Percentage as decimal (e.g., 33.5). |
  | fuel_type | no | string | |
  | fuel_enrichment | no | string | |
  | burnup | no | number | GWd/MTU. |
  | design_status | no | string | Prefer enumerations (Conceptual, Licensed,
  etc.). |
  | mpr_project_ids | no | array of strings | Split if multiple IDs exist. |
  | notes | no | string | |
  | sources | yes | array of strings | |

  ### 3.3 owners_developers

  | Field | Required | Type | Guidance |
  | --- | --- | --- | --- |
  | slug | yes | string | |
  | company_name | yes | string | (company_name). |
  | company_type | no | string | Use enumerations (IOU, COOP, Public Power,
  IPP). |
  | target_customers | no | string | |
  | engagement_level | no | string | From enum (Intrigued, Interested, Invested,
  Inservice). |
  | notes | no | string | |
  | relationship_strength | no | string | Use enum if public. Leave null if
  unknown. |
  | client_priority | no | string | Enum (High, Medium, Low, Strategic,
  Opportunistic). |
  | client_status | no | string | Enum (Active, Warm, Cold, Prospective). |
  | sources | yes | array of strings | |
  | primary_contacts | no | array of personnel.slug | If you identify
  individuals tied to this org. |

  ### 3.4 constructors

  | Field | Required | Type | Guidance |
  | --- | --- | --- | --- |
  | slug | yes | string | |
  | company_name | yes | string | (company_name). |
  | notes | no | string | |
  | sources | yes | array of strings | |

  ### 3.5 operators

  | Field | Required | Type | Guidance |
  | --- | --- | --- | --- |
  | slug | yes | string | |
  | company_name | yes | string | (company_name). |
  | notes | no | string | |
  | sources | yes | array of strings | |

  ### 3.6 offtakers

  | Field | Required | Type | Guidance |
  | --- | --- | --- | --- |
  | slug | yes | string | |
  | organization_name | yes | string | (organization_name). |
  | sector | no | string | Industry sector or vertical. |
  | notes | no | string | |
  | sources | yes | array of strings | |

  ### 3.7 projects

  | Field | Required | Type | Guidance |
  | --- | --- | --- | --- |
  | slug | yes | string | Include location, e.g., "vo-vo-npp-finland". |
  | project_name | yes | string | (project_name). |
  | location | no | string | City/region/country. |
  | project_status | no | string | Use enumerations (Planning, Construction,
  etc.). |
  | licensing_approach | no | string | Use (Research Reactor, Part 50, Part 52)
  when known. |
  | configuration | no | string | Reactor configuration if public. |
  | project_schedule | no | string | Summarize schedule milestones. |
  | target_cod | no | string | ISO date if known. |
  | cod | no | string | Actual COD (ISO date) if in service. |
  | capex | no | number | USD figures; use null if unknown. |
  | opex | no | number | |
  | fuel_cost | no | number | |
  | lcoe | no | number | |
  | mpr_project_id | no | string | |
  | firm_involvement | no | string | Use enumeration (Lead Consultant, etc.)
  where applicable. |
  | project_health | no | string | Use enumeration (On Track, At Risk, etc.). |
  | notes | no | string | |
  | sources | yes | array of strings | |

  ### 3.8 personnel

  | Field | Required | Type | Guidance |
  | --- | --- | --- | --- |
  | slug | yes | string | Include organization for uniqueness ("jane-doe-
  nuscale"). |
  | full_name | yes | string | (full_name). |
  | email | no | string | Use only if publicly available. |
  | phone | no | string | Include international format if known. |
  | role | no | string | Job title. |
  | personnel_type | yes | string | Use enumeration (Internal, Client_Contact,
  Vendor_Contact, Constructor_Contact, Operator_Contact). |
  | organization_slug | no | string | Reference the related entity slug. |
  | organization_type | no | string | One of Owner, Vendor, Constructor,
  Operator, Project. |
  | is_active | yes | boolean | true unless evidence suggests otherwise. |
  | notes | no | string | |
  | sources | yes | array of strings | |

  ## 4. Relationship Collections

  Each relationship object must reference the participating entity slugs and
  include a unique relationship_key (string) to help the importer deduplicate.

  Common fields across relationships:

  | Field | Required | Type | Guidance |
  | --- | --- | --- | --- |
  | relationship_key | yes | string | Deterministic key (e.g., "project-vogtle-
  vendor-westinghouse"). |
  | is_confidential | yes | boolean | Default to false; set true only if the
  relationship is not public. |
  | notes | no | string | Context or qualifiers. |
  | sources | yes | array of strings | URLs backing the relationship.

  Then include type-specific attributes:

  - vendor_supplier_relationships: vendor_slug, supplier_slug, component_type
    (free text or values such as major_component).
  - owner_vendor_relationships: owner_slug, vendor_slug, relationship_type
    (enum: MOU, Development_Agreement, Delivery_Contract).
  - project_vendor_relationships: project_slug, vendor_slug.
  - project_constructor_relationships: project_slug, constructor_slug.
  - project_operator_relationships: project_slug, operator_slug.
  - project_owner_relationships: project_slug, owner_slug.
  - project_offtaker_relationships: project_slug, offtaker_slug, agreement_type,
    contracted_volume.
  - vendor_preferred_constructor: vendor_slug, constructor_slug,
    preference_reason.
  - personnel_entity_relationships: personnel_slug, entity_type, entity_slug,
    role_at_entity.

  ## 5. Data Quality & Sourcing Rules

  - Cite at least one credible, publicly accessible source URL for every entity
    and relationship.
  - Prefer primary sources (company releases, regulator filings) over third-
    party commentary.
  - Never infer confidential values; set them to null if not published.
  - Respect enumerations from the data dictionary; if the published label does
    not map cleanly, leave null and explain in notes.
  - Use consistent currency (USD) and units; specify deviations in notes.

  ## 6. Example (abbreviated)

  {
    "metadata": {
      "generated_at": "2026-01-12T18:42:00Z",
      "researcher": "Research LLM v1.0",
      "scope": ["NuScale Power", "Vogtle Unit 3"],
      "notes": "Summaries derived from 2024 NRC filings and corporate
  disclosures."
    },
    "entities": {
      "technology_vendors": [
        {
          "slug": "nuscale-power",
          "vendor_name": "NuScale Power",
          "notes": "SMR developer headquartered in Portland, Oregon.",
          "sources": ["https://www.nuscale.com/about"]
        }
      ],
      "projects": [
        {
          "slug": "vogtle-unit-3",
          "project_name": "Vogtle Unit 3",
          "location": "Waynesboro, Georgia, United States",
          "project_status": "Operating",
          "licensing_approach": "Part 52",
          "cod": "2023-07-31",
          "project_health": "Operating",
          "notes": "First new US reactor in decades.",
          "sources": ["https://www.southerncompany.com/newsroom/2023-07-31-
  vogtle-unit-3-commercial-operation.html"]
        }
      ]
    },
    "relationships": {
      "project_vendor_relationships": [
        {
          "relationship_key": "vogtle-unit-3-westinghouse",
          "project_slug": "vogtle-unit-3",
          "vendor_slug": "westinghouse-electric",
          "is_confidential": false,
          "notes": "AP1000 reactor technology provider.",
          "sources": ["https://www.nrc.gov/reactors/operating/ops-experience/
  ap1000.html"]
        }
      ]
    }
  }



