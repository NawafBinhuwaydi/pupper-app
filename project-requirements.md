Our customer, Lab Reports, Inc., is based out of Charlotte, NC. Despite their name, Lab Reports, Inc. is not a company that provides laboratory services. Instead, Lab Reports, Inc. is a company that collects, analyzes and distributes data __**ONLY about Labrador Retrievers**__.

Lab Reports, Inc. is launching a new application called **Pupper**. Inspired by recent trends in online dating, the team at Lab Reports, Inc. wants to revolutionize the field of dog adoption by providing a more interactive experience to its users. This application allows dog shelters to enter data about Labrador Retrievers currently in their care. Once uploaded, users of the application can use a web interface to browse dogs and give a “wag” or a “growl” vote. The data science team at Lab Reports, Inc will examine data from shelters and users to determine current dog adoption trends.

**Top challenges and requirements:**

* We have paid several celebrities to tweet about our company, and we can expect our application to go “viral” and be subject to extreme and sudden loads with little warning. When we have done this in the past for other applications, we have experienced failure at all layers of our application.
* Security is “job zero” at Lab Reports, Inc. We need to make sure that our application is secure top-to-bottom to ensure that all user data is protected, all company data is protected, and all consumers of our application are authenticated users.
* Anybody should be able to sign up for this application, but only users of the application can access data related to the application.
* Sometimes our users see a dog that is not right for them, but may be right for one of their friends. We need to be able to share links to particular dogs.
* Sometimes our users have a dog that they haven't been able to take a picture of, but still want to let us know is available to adopt. We need to be able to generate an image of a dog based on the description they provide to ensure all dogs can be adopted as quickly as possible.
* We think dogs will be most likely to be adopted if we can try to match our users to the perfect dog. Ideally users could provide us information, and we use that to determine what dog is the best fit for them.
* We are interested in being able to gain insights from the description users provide when uploading a dog.
* Sometimes shelters send us data that is not about Labrador Retrievers. Sometimes shelters send us garbage data that is missing fields or has incorrect data types (e.g., “weight”: “thirty two pounds”). We want to get the most we can out of this data, even if it is in bad shape. We want to provide an interface for shelters to provide us the following information:
    * Shelter (e.g., “Arlington Shelter”)
    * City (e.g., “Arlington”)
    * State (e.g., “VA”)
    * Dog name (e.g., “Fido”)
    * Dog species (e.g., “Labrador Retriever”)
    * Shelter entry date (e.g., “1/7/2019”)
    * Dog description (e.g., “Good boy”)
    * Dog birthday (e.g., “4/23/2014”)
    * Dog weight in pounds (e.g., “32”)
    * Dog color (e.g., “Brown”)
    * Dog photo (e.g., any .png/.jpeg/.jpg)
* We do not want any non-Labrador retrievers to be shown in the Pupper app. Due to our high popularity, this will be a PR disaster.
* For the dog’s privacy, the dog’s name should be encrypted before stored in any datastore. Dog names should not be stored in plaintext on the backend.
* For other applications in the company, we deploy to our development environment once per month. For this application, we will need to deploy to the development environment as frequently as once per day to adapt to changing requirements. Several members of the engineering team expressed concerns about this with regards to:
    * Ensuring only quality code reaches production.
    * Management overhead associated with frequent deploys.
    * Frequent deployments disrupting the user experience.
    * Ability to roll back to previous versions.
* Our data is central to our business. This needs to be protected at all costs. RTO and RPO are both 30 minutes. Because of the risk of AWS regional availability zone outages, we will need to tolerate regional availability zone outages. Eventually, we’d like to be able to expand globally.
* Shelters are very non-technical, but they are the source of our data. We are unsure the best way to authenticate these shelters.

**Statement of Work (SOW):**

Werner has opened up a SOW. Develop a proof-of-concept (POC) solution to present to the client.

* Build an API that allows authenticated users to upload information and animal images currently in their dog shelter.
** When a new listing is submitted, we need to standardize the image sent to us for display in the Pupper app. Alongside the original image, we should store a resized 400x400 .png, and a 50x50 thumbnail .png.
* Build a simple web page and API(s) that allows authenticated users to:
    * Retrieve a particular dog, or retrieve all dogs according to the following restrictions:
        * State: only show dogs in the user’s selected state
        * Max/Min Weight: only show dogs under/over a certain weight
        * Color: only show dogs of a certain color
        * Min/Max Age: only show dogs under/over a certain age
        * Give a “wag” or “growl” to a dog.
        * Retrieve all dogs that a user has given a “wag”.
        * Provide a method to share links and access a particular dog.