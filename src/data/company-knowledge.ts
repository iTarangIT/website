export const companyKnowledge = `
iTarang Technologies is an EV battery life cycle management company. 
We deal with Lithium-ion batteries. 
We source the batteries from OEMs (Original Equipment Manufacturers) and provide them to our dealer network.
We finance, track, maintain, and recycle EV batteries across India.
Our mission is to ensure every battery is tracked from its first charge to its last, providing affordable EMIs for drivers and visibility for lenders.
We cater to E-rickshaw drivers by providing Lithium-ion batteries on affordable EMIs.
`;

export function getContextForQuery(query: string): string {
    // For now, this just returns all our basic knowledge. 
    // RAG text-matching logic can be expanded here as the knowledge base grows.
    return companyKnowledge;
}
