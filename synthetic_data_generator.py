#!/usr/bin/env python3
"""
Synthetic Clinical Case Generator for Therapy Assistant Agent
Generates realistic patient cases for testing diagnostic algorithms.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import uuid

@dataclass
class PatientDemographics:
    age: int
    gender: str
    ethnicity: str
    occupation: str
    education_level: str
    marital_status: str
    living_situation: str

@dataclass
class ClinicalCase:
    case_id: str
    patient_demographics: PatientDemographics
    presenting_complaint: str
    history_present_illness: str
    past_psychiatric_history: str
    past_medical_history: str
    family_history: str
    social_history: str
    mental_status_exam: str
    primary_diagnosis: str
    secondary_diagnoses: List[str]
    dsm5_criteria_met: List[str]
    icd11_code: str
    severity: str
    duration: str
    functional_impairment: str
    treatment_recommendations: List[str]
    created_date: str

class SyntheticDataGenerator:
    def __init__(self):
        self.demographics_data = self._load_demographics_templates()
        self.disorder_templates = self._load_disorder_templates()
        
    def _load_demographics_templates(self) -> Dict:
        """Load demographic variation templates"""
        return {
            "ages": list(range(18, 80)),
            "genders": ["Male", "Female", "Non-binary"],
            "ethnicities": [
                "Caucasian", "African American", "Hispanic/Latino", 
                "Asian", "Native American", "Middle Eastern", "Mixed"
            ],
            "occupations": [
                "Student", "Teacher", "Healthcare Worker", "Engineer", 
                "Retail Worker", "Manager", "Artist", "Unemployed",
                "Retired", "Self-employed", "Social Worker", "Lawyer"
            ],
            "education_levels": [
                "High School", "Some College", "Bachelor's Degree",
                "Master's Degree", "Doctoral Degree", "Trade School"
            ],
            "marital_status": [
                "Single", "Married", "Divorced", "Widowed", 
                "Separated", "In a relationship"
            ],
            "living_situations": [
                "Lives alone", "Lives with partner", "Lives with family",
                "Lives with roommates", "Lives in assisted living",
                "Homeless", "Lives with children"
            ]
        }
    
    def _load_disorder_templates(self) -> Dict:
        """Load clinical templates for each disorder"""
        return {
            "major_depressive_disorder": {
                "primary_diagnosis": "Major Depressive Disorder, Single Episode, Moderate",
                "icd11_code": "6A70.1",
                "core_symptoms": [
                    "Depressed mood most of the day, nearly every day",
                    "Markedly diminished interest or pleasure in activities",
                    "Significant weight loss or gain",
                    "Insomnia or hypersomnia nearly every day",
                    "Psychomotor agitation or retardation",
                    "Fatigue or loss of energy nearly every day",
                    "Feelings of worthlessness or inappropriate guilt",
                    "Diminished ability to think or concentrate",
                    "Recurrent thoughts of death or suicidal ideation"
                ],
                "presenting_complaints": [
                    "Feeling sad and empty for the past several weeks",
                    "Loss of interest in activities I used to enjoy",
                    "Having trouble sleeping and feeling tired all the time",
                    "Difficulty concentrating at work/school",
                    "Feeling hopeless about the future"
                ],
                "treatment_recommendations": [
                    "Cognitive Behavioral Therapy (CBT)",
                    "Consider SSRI medication evaluation",
                    "Behavioral activation techniques",
                    "Sleep hygiene education",
                    "Regular exercise and physical activity",
                    "Safety planning if suicidal ideation present"
                ]
            },
            "generalized_anxiety_disorder": {
                "primary_diagnosis": "Generalized Anxiety Disorder",
                "icd11_code": "6B00",
                "core_symptoms": [
                    "Excessive anxiety and worry about multiple events",
                    "Difficulty controlling the worry",
                    "Restlessness or feeling on edge",
                    "Being easily fatigued",
                    "Difficulty concentrating",
                    "Irritability",
                    "Muscle tension",
                    "Sleep disturbance"
                ],
                "presenting_complaints": [
                    "Constant worrying about everything",
                    "Feeling anxious and on edge most days",
                    "Physical symptoms like muscle tension and fatigue",
                    "Trouble sleeping due to racing thoughts",
                    "Difficulty focusing because of worry"
                ],
                "treatment_recommendations": [
                    "Cognitive Behavioral Therapy (CBT)",
                    "Mindfulness-based stress reduction",
                    "Progressive muscle relaxation",
                    "Consider SSRI or SNRI medication",
                    "Lifestyle modifications (exercise, caffeine reduction)",
                    "Worry time scheduling technique"
                ]
            },
            "ptsd": {
                "primary_diagnosis": "Post-Traumatic Stress Disorder",
                "icd11_code": "6B40",
                "core_symptoms": [
                    "Intrusive memories or flashbacks of traumatic event",
                    "Distressing dreams related to the trauma",
                    "Dissociative reactions (flashbacks)",
                    "Intense psychological distress to trauma cues",
                    "Avoidance of trauma-related stimuli",
                    "Negative alterations in cognition and mood",
                    "Alterations in arousal and reactivity",
                    "Hypervigilance and exaggerated startle response"
                ],
                "presenting_complaints": [
                    "Nightmares and flashbacks of traumatic event",
                    "Avoiding places/people that remind me of the trauma",
                    "Feeling constantly on guard and easily startled",
                    "Emotional numbness and disconnection from others",
                    "Difficulty sleeping and concentrating"
                ],
                "treatment_recommendations": [
                    "Trauma-Focused Cognitive Behavioral Therapy",
                    "Eye Movement Desensitization and Reprocessing (EMDR)",
                    "Prolonged Exposure Therapy",
                    "Consider SSRI medication for symptoms",
                    "Grounding and coping skills training",
                    "Support group participation"
                ]
            },
            "bipolar_disorder": {
                "primary_diagnosis": "Bipolar I Disorder, Most Recent Episode Manic",
                "icd11_code": "6A60.0",
                "core_symptoms": [
                    "Distinct period of elevated or irritable mood",
                    "Increased self-esteem or grandiosity",
                    "Decreased need for sleep",
                    "More talkative than usual",
                    "Flight of ideas or racing thoughts",
                    "Distractibility",
                    "Increase in goal-directed activity",
                    "Risky behavior with potential negative consequences"
                ],
                "presenting_complaints": [
                    "Periods of extremely high energy and mood",
                    "Needing very little sleep but feeling energetic",
                    "Racing thoughts and talking rapidly",
                    "Making impulsive decisions with money/relationships",
                    "History of depressive episodes alternating with mania"
                ],
                "treatment_recommendations": [
                    "Mood stabilizer medication (lithium, valproate)",
                    "Psychoeducation about bipolar disorder",
                    "Cognitive Behavioral Therapy for bipolar disorder",
                    "Sleep hygiene and routine establishment",
                    "Mood monitoring and trigger identification",
                    "Family therapy and support"
                ]
            },
            "adhd": {
                "primary_diagnosis": "Attention-Deficit/Hyperactivity Disorder, Combined Presentation",
                "icd11_code": "6A05.0",
                "core_symptoms": [
                    "Difficulty sustaining attention in tasks",
                    "Careless mistakes in work or activities",
                    "Difficulty organizing tasks and activities",
                    "Avoids tasks requiring sustained mental effort",
                    "Loses things necessary for tasks",
                    "Easily distracted by extraneous stimuli",
                    "Fidgets or squirms in seat",
                    "Difficulty waiting turn in conversations"
                ],
                "presenting_complaints": [
                    "Difficulty concentrating at work/school",
                    "Feeling restless and unable to sit still",
                    "Procrastinating on important tasks",
                    "Forgetting appointments and losing important items",
                    "Interrupting others in conversations"
                ],
                "treatment_recommendations": [
                    "Stimulant medication evaluation",
                    "Cognitive Behavioral Therapy for ADHD",
                    "Organizational skills training",
                    "Time management strategies",
                    "Environmental modifications",
                    "Mindfulness and attention training"
                ]
            },
            "ocd": {
                "primary_diagnosis": "Obsessive-Compulsive Disorder",
                "icd11_code": "6B20",
                "core_symptoms": [
                    "Recurrent and persistent obsessive thoughts",
                    "Thoughts cause marked anxiety or distress",
                    "Repetitive behaviors or mental acts (compulsions)",
                    "Compulsions aimed at reducing anxiety",
                    "Obsessions or compulsions are time-consuming",
                    "Significant distress or impairment in functioning",
                    "Insight that obsessions/compulsions are excessive",
                    "Attempts to suppress or ignore obsessions"
                ],
                "presenting_complaints": [
                    "Intrusive thoughts that won't go away",
                    "Feeling compelled to repeat certain behaviors",
                    "Excessive checking, cleaning, or counting",
                    "Significant time spent on ritualistic behaviors",
                    "Distress when unable to perform compulsions"
                ],
                "treatment_recommendations": [
                    "Exposure and Response Prevention (ERP)",
                    "Cognitive Behavioral Therapy for OCD",
                    "SSRI medication with higher doses",
                    "Mindfulness-based approaches",
                    "Family education and support",
                    "Gradual exposure hierarchy development"
                ]
            }
        }
    
    def generate_demographics(self) -> PatientDemographics:
        """Generate random but realistic demographics"""
        return PatientDemographics(
            age=random.choice(self.demographics_data["ages"]),
            gender=random.choice(self.demographics_data["genders"]),
            ethnicity=random.choice(self.demographics_data["ethnicities"]),
            occupation=random.choice(self.demographics_data["occupations"]),
            education_level=random.choice(self.demographics_data["education_levels"]),
            marital_status=random.choice(self.demographics_data["marital_status"]),
            living_situation=random.choice(self.demographics_data["living_situations"])
        )
    
    def generate_case(self, disorder_type: str, case_number: int = 1) -> ClinicalCase:
        """Generate a complete clinical case for a specific disorder"""
        if disorder_type not in self.disorder_templates:
            raise ValueError(f"Disorder type {disorder_type} not supported")
        
        template = self.disorder_templates[disorder_type]
        demographics = self.generate_demographics()
        
        # Generate case-specific content
        symptoms = random.sample(template["core_symptoms"], k=random.randint(5, len(template["core_symptoms"])))
        presenting_complaint = random.choice(template["presenting_complaints"])
        
        case = ClinicalCase(
            case_id=f"{disorder_type}_{case_number:03d}",
            patient_demographics=demographics,
            presenting_complaint=presenting_complaint,
            history_present_illness=self._generate_history_present_illness(symptoms, demographics),
            past_psychiatric_history=self._generate_past_psychiatric_history(),
            past_medical_history=self._generate_past_medical_history(),
            family_history=self._generate_family_history(),
            social_history=self._generate_social_history(demographics),
            mental_status_exam=self._generate_mental_status_exam(disorder_type),
            primary_diagnosis=template["primary_diagnosis"],
            secondary_diagnoses=self._generate_secondary_diagnoses(),
            dsm5_criteria_met=symptoms,
            icd11_code=template["icd11_code"],
            severity=random.choice(["Mild", "Moderate", "Severe"]),
            duration=self._generate_duration(),
            functional_impairment=self._generate_functional_impairment(),
            treatment_recommendations=template["treatment_recommendations"],
            created_date=datetime.now().isoformat()
        )
        
        return case
    
    def _generate_history_present_illness(self, symptoms: List[str], demographics: PatientDemographics) -> str:
        """Generate realistic history of present illness"""
        duration = random.choice(["2 weeks", "1 month", "3 months", "6 months", "1 year"])
        onset = random.choice(["gradual", "sudden", "following stressful event"])
        
        hpi = f"Patient is a {demographics.age}-year-old {demographics.gender} who presents with a {duration} history of symptoms that began with {onset} onset. "
        hpi += f"Reports the following symptoms: {', '.join(symptoms[:3])}. "
        hpi += "Symptoms have been progressively worsening and significantly impacting daily functioning."
        
        return hpi
    
    def _generate_past_psychiatric_history(self) -> str:
        """Generate past psychiatric history"""
        histories = [
            "No prior psychiatric treatment or hospitalizations.",
            "Previous episode of depression treated with therapy 2 years ago.",
            "History of anxiety treated with medication in the past.",
            "One psychiatric hospitalization 5 years ago.",
            "Family therapy during adolescence for behavioral issues."
        ]
        return random.choice(histories)
    
    def _generate_past_medical_history(self) -> str:
        """Generate past medical history"""
        histories = [
            "No significant medical history.",
            "History of hypertension, well-controlled on medication.",
            "Type 2 diabetes managed with diet and exercise.",
            "Asthma, uses rescue inhaler as needed.",
            "History of migraine headaches."
        ]
        return random.choice(histories)
    
    def _generate_family_history(self) -> str:
        """Generate family psychiatric history"""
        histories = [
            "No known family history of mental illness.",
            "Mother with history of depression.",
            "Father with alcohol use disorder.",
            "Sibling with anxiety disorder.",
            "Maternal grandmother with bipolar disorder."
        ]
        return random.choice(histories)
    
    def _generate_social_history(self, demographics: PatientDemographics) -> str:
        """Generate social history based on demographics"""
        substances = random.choice([
            "Denies tobacco, alcohol, or illicit drug use.",
            "Social alcohol use on weekends.",
            "Former smoker, quit 2 years ago.",
            "Occasional marijuana use."
        ])
        
        return f"{demographics.occupation}, {demographics.education_level}. {demographics.marital_status}, {demographics.living_situation}. {substances}"
    
    def _generate_mental_status_exam(self, disorder_type: str) -> str:
        """Generate mental status exam findings"""
        base_mse = "Alert and oriented x3. Cooperative with interview. "
        
        disorder_specific = {
            "major_depressive_disorder": "Depressed mood, congruent affect. Psychomotor retardation noted. No psychotic symptoms.",
            "generalized_anxiety_disorder": "Anxious mood, tense appearance. Speech slightly rapid. No psychotic symptoms.",
            "ptsd": "Hypervigilant, easily startled. Restricted affect. Describes intrusive memories.",
            "bipolar_disorder": "Elevated mood, grandiose. Pressured speech, flight of ideas. No psychotic symptoms.",
            "adhd": "Restless, difficulty sitting still. Distractible during interview. Mood euthymic.",
            "ocd": "Anxious appearance. Describes intrusive thoughts. Insight intact regarding symptoms."
        }
        
        return base_mse + disorder_specific.get(disorder_type, "Mood and affect appropriate.")
    
    def _generate_secondary_diagnoses(self) -> List[str]:
        """Generate potential secondary diagnoses"""
        secondary = [
            "Insomnia Disorder",
            "Adjustment Disorder with Mixed Anxiety and Depressed Mood",
            "Caffeine Use Disorder, Mild",
            "Social Anxiety Disorder"
        ]
        return random.sample(secondary, k=random.randint(0, 2))
    
    def _generate_duration(self) -> str:
        """Generate symptom duration"""
        return random.choice([
            "2-4 weeks", "1-3 months", "3-6 months", 
            "6-12 months", "1-2 years", "Over 2 years"
        ])
    
    def _generate_functional_impairment(self) -> str:
        """Generate functional impairment description"""
        impairments = [
            "Mild impairment in work performance and social relationships.",
            "Moderate impairment affecting work attendance and family relationships.",
            "Severe impairment requiring time off work and significant relationship strain.",
            "Mild to moderate impact on daily activities and social functioning."
        ]
        return random.choice(impairments)
    
    def generate_dataset(self, cases_per_disorder: int = 5) -> List[ClinicalCase]:
        """Generate a complete dataset with multiple cases per disorder"""
        all_cases = []
        
        for disorder in self.disorder_templates.keys():
            for i in range(1, cases_per_disorder + 1):
                case = self.generate_case(disorder, i)
                all_cases.append(case)
        
        return all_cases
    
    def save_cases_to_json(self, cases: List[ClinicalCase], filename: str):
        """Save cases to JSON file"""
        cases_dict = [asdict(case) for case in cases]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases_dict, f, indent=2, ensure_ascii=False)

# Example usage
if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    
    # Generate 5 cases per disorder (30 total cases)
    cases = generator.generate_dataset(cases_per_disorder=5)
    
    # Save to JSON file
    generator.save_cases_to_json(cases, "synthetic_clinical_cases.json")
    
    print(f"Generated {len(cases)} clinical cases")
    print("Disorders included:", list(generator.disorder_templates.keys()))
    
    # Display one example case
    example_case = cases[0]
    print(f"\nExample case: {example_case.case_id}")
    print(f"Demographics: {example_case.patient_demographics.age}yo {example_case.patient_demographics.gender}")
    print(f"Diagnosis: {example_case.primary_diagnosis}")
    print(f"Presenting complaint: {example_case.presenting_complaint}")