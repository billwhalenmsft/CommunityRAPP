# Ascend

## Engagement Summary
Customer engagement for Ascend — Phase 6 Upstream Procurement Agent suite.  
Conversational Purchase Requisition (PR) agent deployed on Copilot Studio with SAP ECC 6.0 integration.

## Agents

### Backend (RAPP-generated Python)
- `ascend_purchase_requisition_agent.py` — Full PR creation lifecycle: intent → vendor → item → GL coding → approval routing → SAP write (EBAN/EBKN)
- `ascend_pr_status_agent.py` — PR status queries, list, cancel/edit/remind actions
- `ascend_pr_approval_agent.py` — Delegation of Authority (DoA) logic, approval routing, approver interaction, workflow (BUS2105)

### Copilot Studio Native
See `copilot-studio/` for transpiled topics and flows.

## SAP ECC 6.0 Integration
| Area | Tables |
|------|--------|
| Vendor master | LFA1, LFB1, LFM1 |
| Purchasing data | EINA, EINE, EORD, EKKO, EKPO |
| PR create/write | EBAN, EBKN |
| GL / Accounting | T030, SKA1, SKB1, CSKS, AUFK, PRPS |
| Approval / Release | T16FS, T161F, T161G, T161H, T161S |
| Workflow | BUS2105 |

## Status
- [ ] Discovery
- [x] MVP / Requirements (Phase 6 spec received)
- [ ] Agent code generation
- [ ] Copilot Studio transpile
- [ ] Demo
- [ ] Deployment
