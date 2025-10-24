-- Migration 011: Drop legacy entity tables and relationships
-- Created: 2025-10-10
-- Description: Remove all legacy tables after consolidation to unified company schema
-- Version: 11

-- This migration removes tables that are no longer needed after the unified schema migration:
-- - Legacy entity tables: technology_vendors, owner_developers, operators, constructors, offtakers, clients
-- - Legacy relationship junction tables
-- - product table (technology data moved to companies)

BEGIN TRANSACTION;

-- Drop legacy relationship junction tables first (foreign key dependencies)
DROP TABLE IF EXISTS vendor_supplier_relationships;
DROP TABLE IF EXISTS owner_vendor_relationships;
DROP TABLE IF EXISTS project_vendor_relationships;
DROP TABLE IF EXISTS project_constructor_relationships;
DROP TABLE IF EXISTS project_operator_relationships;
DROP TABLE IF EXISTS project_owner_relationships;
DROP TABLE IF EXISTS project_offtaker_relationships;
DROP TABLE IF EXISTS vendor_preferred_constructors;
DROP TABLE IF EXISTS personnel_entity_relationships;
DROP TABLE IF EXISTS entity_team_members;
DROP TABLE IF EXISTS client_owner_relationships;
DROP TABLE IF EXISTS client_project_relationships;
DROP TABLE IF EXISTS client_vendor_relationships;
DROP TABLE IF EXISTS client_operator_relationships;
DROP TABLE IF EXISTS client_personnel_relationships;

-- Drop legacy entity tables
DROP TABLE IF EXISTS technology_vendors;
DROP TABLE IF EXISTS owner_developers;
DROP TABLE IF EXISTS operators;
DROP TABLE IF EXISTS constructors;
DROP TABLE IF EXISTS offtakers;
DROP TABLE IF EXISTS clients;

-- Drop products table (technology data consolidated into companies)
DROP TABLE IF EXISTS products;

-- Update schema version
INSERT INTO schema_version (version, applied_date, applied_by, description)
VALUES (11, datetime('now'), 'system', 'Drop legacy entity tables and relationships');

COMMIT;
