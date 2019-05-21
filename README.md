# Contracts in the next century: Using the blockchain to prevent manipulation in documents #

### Problem: ###
Currently, making a contract with someone or a company always means to have some trust in them. The parties need to trust each other to uphold the contracts points, whether it is executing some labour or paying an agreed amount of money. And many ideas have been implemented to ensure that, however they are either not very secure against manipulation, (e.g. faking my mother’s signature on a sick note for the school) or are somewhat expensive (e. g. storing the documents at a notary’s office so no party can manipulate it). Additionally, many of these ideas usually need the document to exists on paper, which is not very future-proof and could be a problem if an agreement needs to be made quickly with a partner on the other side of the planet or maybe, in a not so distant future, with someone in a station on Mars or Venus. In these scenarios, a binding contract needs to be made in a digital form and be protected against manipulation on either side.

### Solution: ###
Our proposed solution to this problem will use the abilities of the blockchain to protect documents against manipulation from either side and make them digitally signable to eliminate the need for document to exist on paper. This can be done by calculating a checksum of the document with a specific algorithm and cryptographically signing this checksum by each party. These three numbers will then be stored decentralized using a blockchain. Thereby the checksum is unchangeably saved and protected against manipulations and can later be retrieved to verify the documents if uncertainties occur. Additionally, since it is a work in progress, we may include other features and functions which arise from the project.

### Participants: ###
Sebastian Rahe, Tobias Haar, René Lars Wetzelt, Merlin Bleichert, Stefan Pfeiffer and Timon Vogt

### Features (proposed): ###

| Group: Basic Blockchain Script | Est. Workload | Assignees |
|--------------------------------|---------------|-----------|
| *Peer-to-Peer Communication* | 60 | Rene |
| *Storing and retrieving requests* | 50 | Stefan |
| *Verification* | 80 | Tobi |
| *Block mining* | 50 | Merlin |

<br>

| Group: Common User Interface | Est. Workload | Assignees |
|------------------------------|---------------|-----------|
| *User client GUI: Desktop* | 60 | Tobi |
| *User client GUI: App* | 60 | Merlin | 
| *User client GUI: Website* | 50 | Stefan |
| *User client basic functions* | 60 | Timon |
| *Court GUI for verification* | 50 | Stefan |

<br>

| Group: Standards | Est. Workload | Assignees |
|------------------|---------------|-----------|
| *Necessary pdf standard | 10 | Stefan |
| *Which hash algorithm to use?* | 30 | Timon|
| *Which types of official documents are <br> supported (modifications necessary)?* | 30 | Rene |
| *How to pay miners?* | 10 | Merlin |

<br>

| Group: Thought experiments | Est. Workload | Assignees |
|----------------------------|---------------|-----------|
| *Single party contracts (e. g. testaments)* | 10 | Sebastian |
| *Preventing 51%: How to restrict the government?* | 20 | Sebastian |
| *Risks of Shor’s algorithm* | 30 | Timon |
| *Continue operations in the era of quantum computers* | 30 | Timon |
| *Optimization for neutrino-based networks* | 10 | Timon |

<br>

| Group: Testing | Est. Workload | Assignees |
|----------------|---------------|-----------|
| *Basic functionality test: Node* | 20 | Sebastian |
| *Basic functionality test: Network* | 20 | Sebastian |
| *Basic functionality test: HPC* | 20 | Sebastian |
| *Security tests: Hash algorithm* | 30 | Merlin |
| *Security tests: Malicious messages* | 30 | Rene |
| *Security tests: No ASICs possible* | 30 | Timon |

<br>

| Group: Presentation | Est. Workload | Assignees |
|---------------------|---------------|-----------|
| *Group meetings* | 60 | All |
| *Documentation documents* | 60 | All |
| *PowerPoint Presentation* | 30 | All |
| *Talk preparation* | 30 | All |
| *Use case example* | 30 | All |

