"""
Employee Attrition Analytics Pipeline

This script:
1. Loads employee.csv
2. Cleans and saves employee_cleaned.csv
3. Analyses feature importance using Logistic Regression and Random Forest
4. Explores Job Satisfaction, Job Role and Work-Life Balance
5. Examines Company Tenure alongside Monthly Income and Job Satisfaction
6. Trains and evaluates a Random Forest classification model with ROC and confusion matrix plots

Required packages:
    pip install pandas numpy matplotlib scikit-learn
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_curve,
    auc
)


# --------------------------------------------------
# Helper: section header
# --------------------------------------------------
def section(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def main():
    # --------------------------------------------------
    # DATA LOADING AND PREPARATION
    # --------------------------------------------------
    section("DATA LOADING AND PREPARATION")

    # Load original employee.csv (must be in same folder)
    df = pd.read_csv("employee.csv")
    print("Loaded employee.csv with shape:", df.shape)
    print("Columns:", list(df.columns))

    # Drop identifier if present
    if "Employee ID" in df.columns:
        df_clean = df.drop(columns=["Employee ID"])
        print("\nDropped 'Employee ID' column.")
    else:
        df_clean = df.copy()
        print("\nNo 'Employee ID' column to drop.")

    # Quick missing value check
    print("\nMissing values per column:")
    print(df_clean.isna().sum())

    # Save cleaned dataset
    df_clean.to_csv("employee_cleaned.csv", index=False)
    print("\nSaved cleaned dataset as employee_cleaned.csv")

    # Prepare predictors and target variables
    X = df_clean.drop(columns=["Attrition", "Left Or Stayed?"])
    y = df_clean["Attrition"]

    categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()
    numeric_cols = X.select_dtypes(exclude=["object"]).columns.tolist()

    print("\nCategorical columns:", categorical_cols)
    print("Numeric columns:", numeric_cols)

    categorical_transformer = OneHotEncoder(handle_unknown="ignore")
    numeric_transformer = "passthrough"

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", categorical_transformer, categorical_cols),
            ("numeric", numeric_transformer, numeric_cols),
        ]
    )

    # --------------------------------------------------
    # FEATURE IMPORTANCE ANALYSIS
    # --------------------------------------------------
    section("FEATURE IMPORTANCE ANALYSIS (Logistic Regression + Random Forest)")

    # Logistic Regression pipeline
    log_reg_pipe = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("scaler", StandardScaler(with_mean=False)),
            ("classifier", LogisticRegression(max_iter=1000))
        ]
    )

    log_reg_pipe.fit(X, y)
    print("Fitted logistic regression model.")

    # Get encoded feature names
    ohe = log_reg_pipe.named_steps["preprocessor"].named_transformers_["categorical"]
    encoded_cat_features = ohe.get_feature_names_out(categorical_cols)
    all_features = np.concatenate([encoded_cat_features, np.array(numeric_cols)])

    # Logistic coefficients
    coefficients = log_reg_pipe.named_steps["classifier"].coef_[0]
    feature_importance_lr = pd.DataFrame({
        "feature": all_features,
        "coefficient": coefficients
    })
    feature_importance_lr["abs_coeff"] = feature_importance_lr["coefficient"].abs()

    print("\nTop 20 logistic regression features by |coefficient|:")
    print(feature_importance_lr.sort_values("abs_coeff", ascending=False).head(20))

    # Random Forest pipeline
    rf_pipe = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=150,
                random_state=42
            ))
        ]
    )

    rf_pipe.fit(X, y)
    print("\nFitted random forest model for feature importance.")

    rf_clf = rf_pipe.named_steps["classifier"]
    rf_importances = rf_clf.feature_importances_

    feature_importance_rf = pd.DataFrame({
        "feature": all_features,
        "importance": rf_importances
    }).sort_values(by="importance", ascending=False)

    print("\nTop 20 random forest features by importance:")
    print(feature_importance_rf.head(20))

    # Plot top 10 RF feature importances
    top_rf = feature_importance_rf.head(10)
    plt.figure()
    plt.barh(top_rf["feature"], top_rf["importance"])
    plt.gca().invert_yaxis()
    plt.title("Top 10 Feature Importances (Random Forest)")
    plt.tight_layout()
    plt.savefig("top10_rf_importances.png", dpi=300)
    plt.close()
    print("\nSaved plot: top10_rf_importances.png")

    # --------------------------------------------------
    # JOB SATISFACTION, JOB ROLE AND WORK-LIFE BALANCE ANALYSIS
    # --------------------------------------------------
    section("JOB SATISFACTION, JOB ROLE AND WORK-LIFE BALANCE ANALYSIS")

    df_b = df_clean.copy()

    # Ordinal mappings
    job_sat_order = ["Very Low", "Low", "Medium", "High", "Very High"]
    wlb_order = ["Poor", "Fair", "Good", "Excellent"]

    job_sat_map = {k: v + 1 for v, k in enumerate(job_sat_order)}
    wlb_map = {k: v + 1 for v, k in enumerate(wlb_order)}

    df_b["Job Satisfaction Num"] = df_b["Job Satisfaction"].map(job_sat_map)
    df_b["Work-Life Balance Num"] = df_b["Work-Life Balance"].map(wlb_map)

    # Correlation
    corr_js_wlb = df_b["Job Satisfaction Num"].corr(df_b["Work-Life Balance Num"])
    print(f"Correlation between Job Satisfaction and Work-Life Balance: {corr_js_wlb:.3f}")

    # Mean job satisfaction by job role
    mean_js_by_role = (
        df_b.groupby("Job Role")["Job Satisfaction Num"]
        .mean()
        .sort_values(ascending=False)
    )

    print("\nMean Job Satisfaction by Job Role:")
    print(mean_js_by_role)

    # Plot mean job satisfaction by role
    plt.figure()
    plt.bar(mean_js_by_role.index, mean_js_by_role.values)
    plt.title("Mean Job Satisfaction by Job Role")
    plt.ylabel("Job Satisfaction (1=Very Low, 5=Very High)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("mean_job_satisfaction_by_role.png", dpi=300)
    plt.close()
    print("\nSaved plot: mean_job_satisfaction_by_role.png")

    # --------------------------------------------------
    # COMPANY TENURE AND ATTRITION ANALYSIS
    # --------------------------------------------------
    section("COMPANY TENURE, INCOME AND JOB SATISFACTION ANALYSIS (Logistic Regression)")

    df_c = df_clean.copy()
    df_c["Job Satisfaction Num"] = df_c["Job Satisfaction"].map(job_sat_map)

    # Use only three predictors: Company Tenure, Monthly Income, Job Satisfaction Num
    features_c = df_c[["Company Tenure", "Monthly Income", "Job Satisfaction Num"]]
    target_c = df_c["Attrition"]

    # Scale numeric features and fit logistic regression
    lr_c = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000))
        ]
    )

    lr_c.fit(features_c, target_c)
    coefs_c = lr_c.named_steps["classifier"].coef_[0]

    coef_df = pd.DataFrame({
        "feature": ["Company Tenure", "Monthly Income", "Job Satisfaction Num"],
        "coefficient": coefs_c
    })
    coef_df["abs_coeff"] = coef_df["coefficient"].abs()
    coef_df["odds_ratio (approx)"] = np.exp(coef_df["coefficient"])

    print("Logistic regression (scaled) using only 3 predictors:")
    print(coef_df.sort_values("abs_coeff", ascending=False))

    print(
        "\nInterpretation:\n"
        "- Larger |coefficient| means stronger influence on attrition (after scaling).\n"
        "- Negative coefficient: higher value -> LOWER probability of leaving.\n"
        "- Positive coefficient: higher value -> HIGHER probability of leaving."
    )

    # --------------------------------------------------
    # RANDOM FOREST CLASSIFICATION AND MODEL EVALUATION
    # --------------------------------------------------
    section("RANDOM FOREST CLASSIFICATION AND MODEL EVALUATION")

    # Reuse X, y, preprocessor from above
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    rf_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=200,
                random_state=42
            ))
        ]
    )

    rf_model.fit(X_train, y_train)
    print("Fitted Random Forest classification model.")

    y_pred = rf_model.predict(X_test)
    y_prob = rf_model.predict_proba(X_test)[:, 1]

    # Classification report & confusion matrix
    print("\nClassification report:\n")
    print(classification_report(y_test, y_pred))

    cm = confusion_matrix(y_test, y_pred)
    print("Confusion matrix:")
    print(cm)

    # ROC curve & AUC
    fpr, tpr, thresholds = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    print(f"\nROC AUC: {roc_auc:.3f}")

    # ROC plot
    plt.figure()
    plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - Random Forest Attrition Model")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig("rf_roc_curve.png", dpi=300)
    plt.close()
    print("Saved plot: rf_roc_curve.png")

    # Confusion matrix plot
    plt.figure()
    plt.imshow(cm, interpolation="nearest")
    plt.title("Confusion Matrix - Random Forest Attrition Model")
    plt.colorbar()
    tick_marks = range(2)
    plt.xticks(tick_marks, ["Stayed (0)", "Left (1)"])
    plt.yticks(ticks=tick_marks, labels=["Stayed (0)", "Left (1)"])
    plt.ylabel("True label")
    plt.xlabel("Predicted label")

    # Add numbers to cells
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, cm[i, j], ha="center", va="center")

    plt.tight_layout()
    plt.savefig("rf_confusion_matrix.png", dpi=300)
    plt.close()
    print("Saved plot: rf_confusion_matrix.png")

    section("ANALYSIS COMPLETE.")


if __name__ == "__main__":
    main()
