#!/usr/bin/env python3
import aws_cdk as cdk
from infra.pupper_cdk_stack_simple import PupperCdkStack
from infra.pupper_frontend_stack_fixed import PupperFrontendStack

app = cdk.App()

# Deploy backend infrastructure
backend_stack = PupperCdkStack(
    app,
    "PupperBackendStack",
    description="Pupper Dog Adoption API Backend Infrastructure"
)

# Deploy frontend infrastructure
frontend_stack = PupperFrontendStack(
    app,
    "PupperFrontendStack",
    description="Pupper Dog Adoption App Frontend Infrastructure"
)

# Add tags to all resources
cdk.Tags.of(app).add("Project", "Pupper")
cdk.Tags.of(app).add("Environment", "Production")

app.synth()
