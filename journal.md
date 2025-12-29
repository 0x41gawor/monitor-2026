# 2025-12-28

Schema sections:
- Sleep
- Heart
- Training
- Steps
- Date
- Weight
- Diet

Schema super-sections:
- Regen
- Activity
- Weight
- Diet

Schema Subscetions:
```sh
- Regen
    - Sleep
        - time
            - startTime [ts]
            - endTime [ts]
            - timeAsleep [h]
            - timeInBed [h]
        - efficiency [%]
        - stages
            - deep [h]
            - light [h]
            - rem [h]
            - wake [h]
    - Heart
        - HRV [ms] 
        - RHR [bpm]
- Activity
    - Training 
        - Type [txt] # manually
        - Load [%]   # manually
    - NEAT
        - Steps [1]
- Weight
    - Date [Date]    
    - Weight [kg]    # manually
- Diet 
    - Cal. [kcal]
    - Prot. [g]
    - Fats. [g]
    - Carb. [g]
```

Jak się dostać do Fitbit API? -> [1 - Intro and accessing FitBit API with Postman - FitBit API for Beginners](https://youtu.be/e5WYfIqt_Zk?si=z8fNUBzy5bypgUQ_).