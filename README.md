# AI_Agent

# Work
## ✅ 2025-07-08

- [X] 1. CREWAI 설치 및 실행
- [X] 2. AGENT 추가 : 보고서 한글 번역 AGENT 추가 
- [X] 3. FAST API 추가 : 동적으로 CREWAI 를 호출하기 위해 Fast API 적용 ( 리팩토링 필요 )
- [X] 4. CREWAI 를 활용한 프로젝트 아이디어 추가 

**1. CREWAI 설치 및 실행**
![alt text](image-1.png)

**2. AGENT 추가**

**agents.yaml**
```yaml
translator:
  role: >
    Korean Translator
  goal: >
    Translate all results and reports from previous agents into Korean.
  backstory: >
    You are a translation expert with an excellent ability to accurately and
    naturally convert given English text into Korean. You are known for
    perfectly capturing all technical terms and nuances in your translations.
```

**tasks.yaml**
```yaml
translation_task:
  description: >
    Translate the entire report provided into natural and accurate Korean.
    Ensure all sections, headings, and details are translated while maintaining
    the original meaning and nuance, especially for technical terms.
    The translated report should be ready for presentation.
  expected_output: >
    A fully translated report in Korean, formatted as markdown.
  agent: translator 
```

**crew.py**
```python
    @agent
    def translator(self) -> Agent:
        return Agent(
            config=self.agents_config['translator'], # type: ignore[index]
            verbose=True
        )

...
    @task
    def translation_task(self) -> Task:
        return Task(
            config=self.tasks_config['translation_task'], # type: ignore[index]
            output_file='report_korean.md', # 번역된 파일 저장 경로
            context=[self.reporting_task()] # reporting_task의 결과를 translation_task의 컨텍스트로 전달
        )

...
    @crew
    def crew(self) -> Crew:
        """Creates the CrewAiDemo crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=[
                self.research_task(),
                self.reporting_task(),
                self.translation_task() # <-- translation_task를 태스크 파이프라인에 추가
            ],
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )


```

**3. FAST API 추가**
![alt text](image.png)

**4. CREWAI 를 활용한 프로젝트 아이디어 추가**
```
Account의 고객명 ( 기업 이름 )을 사용합니다.
1. 제무제표 분석 결과 ( 저번 분기 대비, 전년 동일 분기 대비 ) 
2. 최신 뉴스 요약 및 뉴스 URL 
3. 동종 업계 비교  

해당 정보들을 가공하여 제공합니다.
```





***

## SETTING 

**가상화 설정**   
> ```
> py -3.10 -m venv venv // -3.10 은 설치된 파이썬 버전, 두번째 venv : 가상머신 이름
> ```



**가상화 실행 ( 가상 머신이 적용된 디렉토리에서 )**
>```
>.\venv\Scripts\activate 혹은 .\venv\Scripts\Activate.ps1
>```



### CREW AI OPERATE
>```
>crewai install
>crewai run
>```


### APP OPERATE
```commandline
uvicorn src.crew_ai_demo.main:app --reload --host 0.0.0.0 --port 8000
```
```mermaid
erDiagram

  Member ||--o{ Order : places
  Member ||--o{ MemberRole : has
  Role ||--o{ MemberRole : assigned_to

  Order ||--o{ OrderLineItem : contains
  ProductVariant ||--o{ OrderLineItem : part_of

  Product ||--o{ ProductOption : has
  ProductOption ||--o{ ProductOptionValue : has
  Product ||--o{ ProductVariant : defines
  ProductVariant ||--o{ ProductVariantOption : composed_of
  ProductOptionValue ||--o{ ProductVariantOption : used_in

  ProductVariant ||--o{ PriceBookEntry : priced_by
  PriceBook ||--o{ PriceBookEntry : contains

  Product }o--|| Category : belongs_to
  Category ||--o{ Category : parent_of

  %% Entity Definitions
  Member {
    int Id PK
    string email
    string password
    string nick
    string refresh_token
  }

  Role {
    int Id PK
    string title
    string authority
  }

  MemberRole {
    int Id PK
    int member_id FK
    int role_id FK
  }

  Order {
    int Id PK
    int member_id FK
    float total_amount
    datetime order_date
    string shipping_address
  }

  OrderLineItem {
    int Id PK
    int order_id FK
    int product_variant_id FK
    int quantity
    float price_at_time_of_order
  }

  Product {
    int Id PK
    string title
    string description
    int category_id FK
  }

  Category {
    int Id PK
    string title
    int parent_id FK
    int layer
  }

  ProductOption {
    int Id PK
    int product_id FK
    string name
  }

  ProductOptionValue {
    int Id PK
    int product_option_id FK
    string value
  }

  ProductVariant {
    int Id PK
    int product_id FK
    string sku
    int inventory_quantity
    string image_url
    float price_adjustment
  }

  ProductVariantOption {
    int Id PK
    int product_variant_id FK
    int product_option_value_id FK
  }

  PriceBook {
    int Id PK
    string title
  }

  PriceBookEntry {
    int Id PK
    int pricebook_id FK
    int product_variant_id FK
    float price
  }

```

## Build
```commandline
docker build -t ai_test .
```

## requirements.txt 추출하는 방법
```bash
pip freeze > requirements.txt
```

## ERROR
```commandline
-----
 > [4/5] RUN pip install --no-cache-dir -r requirements.txt:
1.909 Obtaining ai_test from git+https://github.com/GustavEiffels/AI_Agent.git@8c6c8af07368aed7ef4f08af3f3565ea3c38b207#egg=ai_test&subdirectory=ai_test (from -r requirements.txt (line 1))
1.909   Cloning https://github.com/GustavEiffels/AI_Agent.git (to revision 8c6c8af07368aed7ef4f08af3f3565ea3c38b207) to ./src/ai-test
1.910   ERROR: Error [Errno 2] No such file or directory: 'git' while executing command git version
1.910 ERROR: Cannot find command 'git' - do you have 'git' installed and in your PATH?
2.151
2.151 [notice] A new release of pip is available: 23.0.1 -> 25.1.1
2.151 [notice] To update, run: pip install --upgrade pip
------
dockerfile:4
--------------------
   2 |     WORKDIR /app
   3 |     COPY requirements.txt .
   4 | >>> RUN pip install --no-cache-dir -r requirements.txt
   5 |     COPY . /app
   6 |
--------------------
ERROR: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/cif0pavj1p6umntn1n8vh7h56
(venv) PS C:\Users\SIUK\AI_Agent\ai_test> 


```
> 이 줄은 pip에게 requirements.txt 파일의 첫 번째 줄에서 ai_test라는 패키지를 Git 저장소(https://github.com/GustavEiffels/AI_Agent.git) 에서 직접 다운로드하여 설치하라고 지시하고 있습니다.
pip이 Git 저장소에서 패키지를 설치하려면, 컨테이너 내부에도 git 클라이언트가 설치되어 있어야 합니다. 하지만 여러분의 Dockerfile은 git을 설치하는 지시를 포함하고 있지 않습니다.

## Error 02 
```commandline
(venv) PS C:\Users\SIUK\AI_Agent\ai_test> docker build -t ai_test .
[+] Building 0.3s (1/1) FINISHED                                                                                                                                                                                                                                                            docker:desktop-linux
 => [internal] load build definition from dockerfile                                                                                                                                                                                                                                                        0.0s
 => => transferring dockerfile: 336B                                                                                                                                                                                                                                                                        0.0s 
dockerfile:12
--------------------
  10 |     CMD ["uvicorn", "src.ai_test.main:app", "--host", "0.0.0.0", "--port", "8000"]
  11 |
  12 | >>> // docker build -t ai_test .
--------------------
ERROR: failed to solve: dockerfile parse error on line 12: unknown instruction: //

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/ema12ynq7ish7d5og2rk128ie
(venv) PS C:\Users\SIUK\AI_Agent\ai_test> 

```
> 12번째 줄에 // docker build -t ai_test . 라는 내용이 있고, //가 Dockerfile에서 알 수 없는 명령어라고 나오고 있습니다. 제가 이전에 설명하려고 넣었던 예시 명령어가 실수로 Dockerfile 내용에 포함된 것 같습니다.