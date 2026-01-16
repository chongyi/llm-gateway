/**
 * Model-Provider Mapping Form Component
 * Used for configuring providers for a model
 */

'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { useForm, Controller, useFieldArray } from 'react-hook-form';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { RuleBuilder } from '@/components/common';
import {
  ModelMappingProvider,
  ModelMappingProviderCreate,
  ModelMappingProviderUpdate,
  Provider,
  RuleSet,
} from '@/types';

interface ModelProviderFormProps {
  /** Whether dialog is open */
  open: boolean;
  /** Dialog close callback */
  onOpenChange: (open: boolean) => void;
  /** Current requested model name */
  requestedModel: string;
  /** Available provider list */
  providers: Provider[];
  /** Default prices from model fallback (for create mode prefill) */
  defaultPrices?: { input_price?: number | null; output_price?: number | null };
  /** Mapping data for edit mode */
  mapping?: ModelMappingProvider | null;
  /** Submit callback */
  onSubmit: (data: ModelMappingProviderCreate | ModelMappingProviderUpdate) => void;
  /** Loading state */
  loading?: boolean;
}

/** Form Field Definition */
interface FormData {
  provider_id: string;
  target_model_name: string;
  provider_rules: RuleSet | null;
  billing_mode: 'token_flat' | 'token_tiered' | 'per_request';
  // token_flat
  token_price: string;
  separate_io: boolean;
  input_price: string;
  output_price: string;
  // per_request
  per_request_price: string;
  // token_tiered
  tiers: Array<{ max_input_tokens: string; token_price: string }>;
  priority: number;
  weight: number;
  is_active: boolean;
}

/**
 * Model-Provider Mapping Form Component
 */
export function ModelProviderForm({
  open,
  onOpenChange,
  requestedModel,
  providers,
  defaultPrices,
  mapping,
  onSubmit,
  loading = false,
}: ModelProviderFormProps) {
  // Check if edit mode
  const isEdit = !!mapping;
  
  // Form control
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    control,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      provider_id: '',
      target_model_name: '',
      provider_rules: null,
      billing_mode: 'token_flat',
      token_price: '',
      separate_io: false,
      input_price: '',
      output_price: '',
      per_request_price: '',
      tiers: [{ max_input_tokens: '32768', token_price: '' }],
      priority: 0,
      weight: 1,
      is_active: true,
    },
  });

  const { fields: tierFields, append: appendTier, remove: removeTier } = useFieldArray({
    control,
    name: 'tiers',
  });

  const providerId = watch('provider_id');
  const isActive = watch('is_active');
  const billingMode = watch('billing_mode');
  const separateIO = watch('separate_io');
  const tokenPrice = watch('token_price');

  // Fill form data in edit mode
  useEffect(() => {
    if (mapping) {
      const mode = (mapping.billing_mode || 'token_flat') as
        | 'token_flat'
        | 'token_tiered'
        | 'per_request';

      const legacyHasSeparateIO =
        mode === 'token_flat' &&
        mapping.input_price !== null &&
        mapping.input_price !== undefined &&
        mapping.output_price !== null &&
        mapping.output_price !== undefined &&
        mapping.input_price !== mapping.output_price;

      const tokenPriceValue =
        legacyHasSeparateIO
          ? ''
          : mapping.input_price !== null && mapping.input_price !== undefined
            ? String(mapping.input_price)
            : mapping.output_price !== null && mapping.output_price !== undefined
              ? String(mapping.output_price)
              : defaultPrices?.input_price === null || defaultPrices?.input_price === undefined
                ? '0'
                : String(defaultPrices.input_price);

      reset({
        provider_id: String(mapping.provider_id),
        target_model_name: mapping.target_model_name,
        provider_rules: mapping.provider_rules || null,
        billing_mode: mode,
        token_price: tokenPriceValue,
        separate_io: legacyHasSeparateIO,
        input_price:
          mapping.input_price === null || mapping.input_price === undefined
            ? defaultPrices?.input_price === null || defaultPrices?.input_price === undefined
              ? '0'
              : String(defaultPrices.input_price)
            : String(mapping.input_price),
        output_price:
          mapping.output_price === null || mapping.output_price === undefined
            ? defaultPrices?.output_price === null || defaultPrices?.output_price === undefined
              ? '0'
              : String(defaultPrices.output_price)
            : String(mapping.output_price),
        per_request_price:
          mapping.per_request_price === null || mapping.per_request_price === undefined
            ? '0'
            : String(mapping.per_request_price),
        tiers:
          mapping.tiered_pricing && mapping.tiered_pricing.length > 0
            ? mapping.tiered_pricing.map((t) => ({
                max_input_tokens:
                  t.max_input_tokens === null || t.max_input_tokens === undefined
                    ? ''
                    : String(t.max_input_tokens),
                token_price: String(t.input_price),
              }))
            : [{ max_input_tokens: '32768', token_price: tokenPriceValue }],
        priority: mapping.priority,
        weight: mapping.weight,
        is_active: mapping.is_active,
      });
    } else {
      const fallbackTokenPrice =
        defaultPrices?.input_price === null || defaultPrices?.input_price === undefined
          ? '0'
          : String(defaultPrices.input_price);
      reset({
        provider_id: '',
        target_model_name: '',
        provider_rules: null,
        billing_mode: 'token_flat',
        token_price: fallbackTokenPrice,
        separate_io: false,
        input_price: fallbackTokenPrice,
        output_price:
          defaultPrices?.output_price === null || defaultPrices?.output_price === undefined
            ? fallbackTokenPrice
            : String(defaultPrices.output_price),
        per_request_price: '0',
        tiers: [{ max_input_tokens: '32768', token_price: fallbackTokenPrice }],
        priority: 0,
        weight: 1,
        is_active: true,
      });
    }
  }, [defaultPrices?.input_price, defaultPrices?.output_price, mapping, reset]);

  // Keep token_flat unified price in sync with input/output when not using separate I/O pricing
  useEffect(() => {
    if (billingMode !== 'token_flat' || separateIO) return;
    setValue('input_price', tokenPrice || '0');
    setValue('output_price', tokenPrice || '0');
  }, [billingMode, separateIO, setValue, tokenPrice]);

  // Submit form
  const onFormSubmit = (data: FormData) => {
    const billingMode = data.billing_mode;

    const buildFlatPricing = () => {
      if (data.separate_io) {
        const inputPrice = data.input_price.trim();
        const outputPrice = data.output_price.trim();
        return {
          input_price: inputPrice ? Number(inputPrice) : null,
          output_price: outputPrice ? Number(outputPrice) : null,
        };
      }
      const tokenPrice = data.token_price.trim();
      const numeric = tokenPrice ? Number(tokenPrice) : 0;
      return { input_price: numeric, output_price: numeric };
    };

    const buildTieredPricing = () => {
      return (data.tiers || [])
        .filter((t) => t.token_price.trim() !== '')
        .map((t) => {
          const price = Number(t.token_price.trim());
          const maxStr = t.max_input_tokens.trim();
          const maxInputTokens = maxStr === '' ? null : Number(maxStr);
          return {
            max_input_tokens: maxInputTokens,
            input_price: price,
            output_price: price,
          };
        });
    };

    if (isEdit) {
      // Update mode
      const submitData: ModelMappingProviderUpdate = {
        target_model_name: data.target_model_name,
        billing_mode: billingMode,
        priority: data.priority,
        weight: data.weight,
        is_active: data.is_active,
      };

      if (billingMode === 'per_request') {
        const perReq = data.per_request_price.trim();
        submitData.per_request_price = perReq ? Number(perReq) : 0;
        submitData.input_price = null;
        submitData.output_price = null;
        submitData.tiered_pricing = null;
      } else if (billingMode === 'token_tiered') {
        submitData.tiered_pricing = buildTieredPricing();
        submitData.per_request_price = null;
        submitData.input_price = null;
        submitData.output_price = null;
      } else {
        const flat = buildFlatPricing();
        submitData.input_price = flat.input_price;
        submitData.output_price = flat.output_price;
        submitData.per_request_price = null;
        submitData.tiered_pricing = null;
      }
      
      submitData.provider_rules = data.provider_rules || undefined;
      
      onSubmit(submitData);
    } else {
      // Create mode
      const submitData: ModelMappingProviderCreate = {
        requested_model: requestedModel,
        provider_id: Number(data.provider_id),
        target_model_name: data.target_model_name,
        billing_mode: billingMode,
        priority: data.priority,
        weight: data.weight,
        is_active: data.is_active,
      };

      if (billingMode === 'per_request') {
        const perReq = data.per_request_price.trim();
        submitData.per_request_price = perReq ? Number(perReq) : 0;
        submitData.input_price = null;
        submitData.output_price = null;
        submitData.tiered_pricing = null;
      } else if (billingMode === 'token_tiered') {
        submitData.tiered_pricing = buildTieredPricing();
        submitData.per_request_price = null;
        submitData.input_price = null;
        submitData.output_price = null;
      } else {
        const flat = buildFlatPricing();
        submitData.input_price = flat.input_price;
        submitData.output_price = flat.output_price;
        submitData.per_request_price = null;
        submitData.tiered_pricing = null;
      }
      
      submitData.provider_rules = data.provider_rules || undefined;
      
      onSubmit(submitData);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? 'Edit Provider Configuration' : 'Add Provider Configuration'}
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
          {/* Requested Model Name (Read Only) */}
          <div className="space-y-2">
            <Label>Requested Model Name</Label>
            <Input value={requestedModel} disabled />
          </div>

          {/* Provider Selection */}
          <div className="space-y-2">
            <Label>
              Provider <span className="text-destructive">*</span>
            </Label>
            {providers.length === 0 && !isEdit ? (
              <div className="text-sm text-muted-foreground p-2 border rounded-md bg-muted/50">
                No available providers, please
                <Link href="/providers" className="text-primary hover:underline mx-1">
                  create a provider
                </Link>
                first.
              </div>
            ) : (
              <Select
                value={providerId}
                onValueChange={(value) => setValue('provider_id', value)}
                disabled={isEdit}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Provider" />
                </SelectTrigger>
                <SelectContent>
                  {providers.map((provider) => (
                    <SelectItem key={provider.id} value={String(provider.id)}>
                      {provider.name} ({provider.protocol})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {!providerId && !isEdit && providers.length > 0 && (
              <p className="text-sm text-destructive">Please select a provider</p>
            )}
          </div>

          {/* Target Model Name */}
          <div className="space-y-2">
            <Label htmlFor="target_model_name">
              Target Model Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="target_model_name"
              placeholder="Actual model name used by this provider, e.g. gpt-4-0613"
              {...register('target_model_name', {
                required: 'Target model name is required',
              })}
            />
            {errors.target_model_name && (
              <p className="text-sm text-destructive">
                {errors.target_model_name.message}
              </p>
            )}
          </div>

          {/* Billing / Pricing */}
          <div className="rounded-lg border bg-muted/30 p-3 space-y-3">
            <div className="text-sm font-medium">Billing</div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Billing Mode</Label>
                <Select
                  value={billingMode}
                  onValueChange={(value) =>
                    setValue('billing_mode', value as FormData['billing_mode'])
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select billing mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="per_request">Per request</SelectItem>
                    <SelectItem value="token_flat">Per token (flat)</SelectItem>
                    <SelectItem value="token_tiered">Per token (tiered by input tokens)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {billingMode === 'per_request' ? (
              <div className="space-y-2">
                <Label htmlFor="per_request_price">Price (USD / request)</Label>
                <Input
                  id="per_request_price"
                  type="number"
                  min={0}
                  step="0.0001"
                  {...register('per_request_price')}
                />
              </div>
            ) : billingMode === 'token_tiered' ? (
              <div className="space-y-3">
                <div className="text-xs text-muted-foreground">
                  Choose the price based on input tokens, then apply the same price to input/output tokens.
                </div>
                <div className="space-y-2">
                  {tierFields.map((field, idx) => (
                    <div key={field.id} className="grid grid-cols-5 gap-2 items-end">
                      <div className="col-span-2 space-y-1">
                        <Label>Max Input Tokens</Label>
                        <Input
                          type="number"
                          min={1}
                          placeholder="e.g. 32768 (empty = no limit)"
                          {...register(`tiers.${idx}.max_input_tokens` as const)}
                        />
                      </div>
                      <div className="col-span-2 space-y-1">
                        <Label>Price (USD / 1M tokens)</Label>
                        <Input
                          type="number"
                          min={0}
                          step="0.0001"
                          placeholder="e.g. 1.2"
                          {...register(`tiers.${idx}.token_price` as const)}
                        />
                      </div>
                      <div className="col-span-1 flex gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => removeTier(idx)}
                          disabled={tierFields.length <= 1}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => appendTier({ max_input_tokens: '', token_price: '' })}
                  >
                    Add Tier
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="token_price">Price (USD / 1M tokens)</Label>
                  <Input
                    id="token_price"
                    type="number"
                    min={0}
                    step="0.0001"
                    {...register('token_price')}
                    disabled={separateIO}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="separate_io">Separate input/output pricing</Label>
                  <Switch
                    id="separate_io"
                    checked={separateIO}
                    onCheckedChange={(checked) => setValue('separate_io', checked)}
                  />
                </div>

                {separateIO && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="input_price">Input Price (USD / 1M tokens)</Label>
                      <Input
                        id="input_price"
                        type="number"
                        min={0}
                        step="0.0001"
                        {...register('input_price')}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="output_price">Output Price (USD / 1M tokens)</Label>
                      <Input
                        id="output_price"
                        type="number"
                        min={0}
                        step="0.0001"
                        {...register('output_price')}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            <p className="text-xs text-muted-foreground">
              Billing is applied when this request routes to the selected provider.
            </p>
          </div>

          {/* Priority and Weight */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Input
                id="priority"
                type="number"
                min={0}
                {...register('priority', { valueAsNumber: true })}
              />
              <p className="text-sm text-muted-foreground">Lower value means higher priority</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="weight">Weight</Label>
              <Input
                id="weight"
                type="number"
                min={1}
                {...register('weight', { valueAsNumber: true })}
              />
            </div>
          </div>

          {/* Provider Level Rules */}
          <div className="space-y-2">
            <Label>Provider Level Rules (Beta)</Label>
            <Controller
              name="provider_rules"
              control={control}
              render={({ field }) => (
                <RuleBuilder
                  value={field.value || undefined}
                  onChange={field.onChange}
                />
              )}
            />
          </div>

          {/* Status */}
          <div className="flex items-center justify-between">
            <Label htmlFor="is_active">Enabled Status</Label>
            <Switch
              id="is_active"
              checked={isActive}
              onCheckedChange={(checked) => setValue('is_active', checked)}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading || (!isEdit && !providerId)}
            >
              {loading ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
