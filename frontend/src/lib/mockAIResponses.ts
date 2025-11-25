export const mockAIResponses = [
  "I'm analyzing your claim details. Based on the documents provided, this looks like a straightforward medical reimbursement case.",
  "Your claim appears to be within policy limits. All required documents are present.",
  "I recommend submitting additional supporting documentation to strengthen your claim.",
  "The average processing time for similar claims is 3-5 business days.",
  "Based on historical data, claims in this category have a 92% approval rate.",
  "Would you like me to explain any specific part of the claims process?",
  "I can help you track the status of your claim or answer questions about required documentation.",
];

export function getMockAIResponse(message: string): string {
  const lowerMessage = message.toLowerCase();
  
  if (lowerMessage.includes('status')) {
    return "Your current claim is under review. The claims team typically takes 2-3 business days to process medical reimbursements. I'll notify you as soon as there's an update!";
  }
  
  if (lowerMessage.includes('document') || lowerMessage.includes('upload')) {
    return "For medical claims, you'll need: 1) Original hospital/pharmacy bill, 2) Prescription (if applicable), 3) Payment receipt. Make sure all documents are clear and legible!";
  }
  
  if (lowerMessage.includes('policy') || lowerMessage.includes('limit')) {
    return "Your medical reimbursement policy covers up to $150,000 per year. You've currently used $32,450 of your annual limit. Emergency medical expenses have no upper limit with prior intimation.";
  }
  
  if (lowerMessage.includes('how') || lowerMessage.includes('process')) {
    return "The claims process is simple: 1) Upload your documents, 2) AI pre-verification (instant), 3) Human review (1-2 days), 4) Approval & payment (2-3 days). Most claims are resolved within a week!";
  }
  
  // Default responses
  const randomIndex = Math.floor(Math.random() * mockAIResponses.length);
  return mockAIResponses[randomIndex];
}
