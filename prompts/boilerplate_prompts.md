# Prompts used to get the boilerplate (reusable)

Use these in order (or by section) when starting a similar migration/BI-to-LookML project. Reference `docs/code_layout.md` and `docs/migration_architecture.png` in the repo.

---

## 1. Understand existing architecture

- **Understand the diagram**  
  `understand @docs/migration_architecture.png`

- **Current code layout**  
  `current code src`

---

## 2. Decide to redesign (without touching code yet)

- **Plan redesign, don’t touch src**  
  `I dont like the current src code architecture we should work on it lets not touch src`

- **Brainstorm then document**  
  `lets brainstorm and then we will add code arch layout docs`

- **Keep answers short**  
  `you're generating too much t of information`

---

## 3. Metadata collector

- **Define collector responsibilities**  
  `lets discuss about metadata collector
  1. List metadata (list reports in server)
  2. Download metadata (different for each bi)
  3. extract metadata
  now tell how to structure this alone anything to add (consider this is a library)`

- **Architecture and patterns**  
  `what code arch and design pattern can used to implement this (not over engineered)`

- **Version/license differences**  
  `but sometimes metadata extraction different for each version / vs license`

- **One approach, extendable later**  
  `lets consider 1 approach for now but can extend`

- **Folder structure**  
  `what is folder structure`

- **Generic names**  
  `powerbi_collector can the names be generic`

- **API/CLI and parallelization**  
  `so we can use this in api/cli and parallelize??`

- **Document and small tweaks**  
  `please do the tweak and add the in documentations for code layout docs`

---

## 4. Parser & normalizer

- **Brainstorm parser/normalizer**  
  `can we go for brainstorm module ??? parser and normalize`

- **One module, canonical output, input sources**  
  `its one module expected output is canonical model and input is metadata downloaded in previous step or metadata collected outside and store in file (local) gcs path (cloud). got it??
  semantic layer -> canonical mapping: datasources, table, custom sql, relationship - dimension, measure, calc fields
  visualization -> canonical mapping: viz type, fields used, styles etc
  dashboard -> canonical mapping: components and arrangement properties
  available in src/model for ur idea`

- **Code structure**  
  `what is code structure`

- **Handlers and orchestrator**  
  `semantic we would need separate handler for dimension measure calc fields dashboard and orchestrate to do this`

- **Keep it manageable**  
  `I will let you make decision not over engineered and make code manageable`

- **YAML for rules**  
  `we need yaml to manage rules for raw -> canonical should we use separate yaml for semantic and viz??`

- **Add to code layout doc**  
  `go ahead and add the code layout`

---

## 5. Transformer

- **Discuss transformer**  
  `can we discuss about transformer`

- **Clarify: transformer vs writing files**  
  `Transformer = "canonical in -> LookML terms out". No writing files. (nope we need to write some files)???`

- **Separate transformer and generator**  
  `we should separate as transformer gonna be complex`

- **Folder structure in sync with canonical**  
  `what is folder structure (in synch with canonical??`

- **Helpers, common utils, transformer YAML**  
  `go ahead add helper wherever required and common utils to re-use across all 4 modules, yaml for transformer too`

- **Update code layout**  
  `go ahead and update the code layout`

---

## 6. Archive and new boilerplate

- **Archive before replacing**  
  `before creating new boiler did we deleted and archived?`

- **Delete old code**  
  `yes please what is point of doing new boiler plate if u dont delete.`

- **Full reset and regenerate**  
  `can you remove src folder completely and regenerate`

---

## 7. Reuse prompts (this file)

- **Save prompts for reuse**  
  `can we add list of prompts that i used to get boiler plate can be reused in new prompt folder`

---

## How to reuse

1. Create a new repo or branch.
2. Add (or point to) something like `docs/migration_architecture.png` and a short “current code” overview if you have one.
3. Copy the prompts from the section you need (e.g. collector only, or full pipeline) into your chat.
4. Ask for “code layout in docs” first, then “implement boilerplate with dummy/placeholder files” when ready.
5. Optionally add “archive current src and tests/scripts, then regenerate” so old code is preserved and `src` is clean.
